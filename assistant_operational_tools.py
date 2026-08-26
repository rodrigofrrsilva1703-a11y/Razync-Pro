from __future__ import annotations

import re
import unicodedata
from datetime import date, timedelta
from typing import Any

import pandas as pd

from assistant_actions import ActionDraft
from assistant_response_policy import humanize_local_response
from reconciliation_tools import duplicate_groups, smart_invoice_matches


def _plain(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _money(value: Any) -> str:
    return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _date_hint(text: str, today: date) -> date | None:
    plain = _plain(text)
    if "ontem" in plain:
        return today - timedelta(days=1)
    if "hoje" in plain:
        return today
    match = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", plain)
    if not match:
        return None
    year = int(match.group(3) or today.year)
    if year < 100:
        year += 2000
    try:
        return date(year, int(match.group(2)), int(match.group(1)))
    except ValueError:
        return None


def _amounts(text: str) -> list[float]:
    values: list[float] = []
    for raw in re.findall(r"(?:r\$\s*)?(\d+(?:\.\d{3})*(?:,\d{1,2})|\d+(?:[.,]\d{1,2})?)", text, flags=re.I):
        normalized = raw.replace(".", "").replace(",", ".") if "," in raw else raw
        try:
            values.append(float(normalized))
        except ValueError:
            continue
    return values


def search_business_records(
    query: str,
    *,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    limit: int = 8,
) -> list[dict[str, Any]]:
    needle = _plain(query)
    ignored = {"buscar", "busque", "procure", "procurar", "mostrar", "mostre", "encontre", "achar", "por", "de", "da", "do", "o", "a"}
    tokens = [token for token in re.findall(r"[a-z0-9@._/-]+", needle) if len(token) > 1 and token not in ignored]
    results: list[dict[str, Any]] = []

    def add(kind: str, route: str, item: dict, fields: list[str], title: str, detail: str) -> None:
        haystack = _plain(" ".join(str(item.get(field) or "") for field in fields))
        score = sum(token in haystack for token in tokens)
        if tokens and score:
            results.append({"kind": kind, "route": route, "id": item.get("id"), "title": title, "detail": detail, "score": score})

    for item in transactions.to_dict("records") if not transactions.empty else []:
        add("Movimentação", "Movimentações", item, ["description", "category", "counterparty", "document_number", "value"], str(item.get("description") or "Movimentação"), f"{item.get('tx_type', '')} · {_money(item.get('value'))} · {str(item.get('tx_date', ''))[:10]}")
    for item in invoices.to_dict("records") if not invoices.empty else []:
        add("Nota", "Notas Fiscais", item, ["number", "customer", "description", "amount", "status"], f"Nota {item.get('number') or 'sem número'}", f"{item.get('customer') or 'Cliente não informado'} · {_money(item.get('amount'))} · {item.get('status', '')}")
    for item in das_rows:
        add("DAS", "DAS", item, ["competence", "status", "amount", "notes"], f"DAS {item.get('competence') or ''}", f"{item.get('status', '')} · {_money(item.get('amount'))}")
    for item in obligations:
        add("Obrigação", "Obrigações", item, ["title", "category", "status", "notes"], str(item.get("title") or "Obrigação"), f"{item.get('status', '')} · {str(item.get('due_date') or '')[:10]}")
    for item in documents:
        add("Documento", "Documentos", item, ["filename", "category", "reference_month"], str(item.get("filename") or "Documento"), f"{item.get('category', '')} · {item.get('reference_month', '')}")
    return sorted(results, key=lambda item: (-int(item["score"]), str(item["title"])))[:limit]


def answer_record_search(question: str, **snapshot: Any) -> dict[str, Any] | None:
    plain = _plain(question)
    if not any(term in plain for term in ("busque", "procure", "encontre", "onde esta", "localize", "pesquise")):
        return None
    rows = search_business_records(question, **snapshot)
    if not rows:
        answer = humanize_local_response(
            "Não encontrei registros com esses termos. Tente informar número, valor, cliente ou descrição.",
            question=question,
            source="search",
        )
        return {"answer": answer, "confidence": "Alta", "reason": "Busca exata nos dados cadastrados."}
    lines = [f"• **{row['kind']} — {row['title']}**: {row['detail']}" for row in rows]
    answer = humanize_local_response(
        f"Encontrei {len(rows)} resultado(s) que combinam com o seu pedido:\n\n" + "\n".join(lines),
        question=question,
        source="search",
    )
    return {"answer": answer, "confidence": "Alta", "reason": "Busca local por termos nos seus registros.", "route": rows[0]["route"]}


def _transaction_target(question: str, transactions: pd.DataFrame, *, today: date) -> dict[str, Any] | None:
    if transactions.empty:
        return None
    candidates = transactions.copy()
    plain = _plain(question)
    if "despesa" in plain:
        candidates = candidates[candidates["tx_type"] == "Despesa"]
    elif "receita" in plain:
        candidates = candidates[candidates["tx_type"] == "Receita"]
    hinted_date = _date_hint(question, today)
    if hinted_date is not None:
        dates = pd.to_datetime(candidates["tx_date"], errors="coerce").dt.date
        candidates = candidates[dates == hinted_date]
    values = _amounts(question)
    if len(values) >= 2:
        candidates = candidates[(pd.to_numeric(candidates["value"], errors="coerce") - values[0]).abs() < .01]
    words = [word for word in re.findall(r"[a-zá-ú]{4,}", plain) if word not in {"altere", "corrija", "mude", "valor", "para", "despesa", "receita", "ontem", "hoje", "lancamento"}]
    if words and not candidates.empty:
        text_series = candidates["description"].fillna("").astype(str).map(_plain)
        matches = candidates[text_series.map(lambda value: any(word in value for word in words))]
        if not matches.empty:
            candidates = matches
    if len(candidates) != 1:
        return None
    return candidates.iloc[0].to_dict()


def plan_record_operation(question: str, *, transactions: pd.DataFrame, invoices: pd.DataFrame, obligations: list[dict], today: date | None = None) -> ActionDraft | None:
    today = today or date.today()
    plain = _plain(question)
    update_terms = ("altere", "corrija", "mude", "atualize")
    if any(term in plain for term in update_terms) and any(term in plain for term in ("lancamento", "despesa", "receita")):
        target = _transaction_target(question, transactions, today=today)
        if target is None:
            return None
        values = _amounts(question)
        updates: dict[str, Any] = {}
        if len(values) >= 2:
            updates["value"] = values[-1]
        category_match = re.search(r"(?i)categoria\s+([\wÀ-ÿ /-]+?)(?:\.|,|$)", question)
        if category_match:
            updates["category"] = category_match.group(1).strip()[:100]
        if not updates:
            return None
        summary = f"Alterar {target.get('tx_type', 'lançamento').lower()} “{target.get('description', '')}” · {_money(target.get('value'))} → {_money(updates.get('value', target.get('value')))}"
        return ActionDraft("update_transaction", {"record_id": int(target["id"]), "updates": updates, "previous": {key: target.get(key) for key in ("tx_date", "tx_type", "description", "category", "value", "document_number", "counterparty", "payment_method")}}, (), summary, "Busca local")

    if any(term in plain for term in ("conclua", "concluir", "marque como pago", "marque como concluido")) and any(term in plain for term in ("obrigacao", "lembrete", "das")):
        candidates = [row for row in obligations if str(row.get("status") or "").lower() == "pendente"]
        words = [word for word in re.findall(r"[a-zá-ú]{3,}", plain) if word not in {"marque", "como", "pago", "concluido", "obrigacao", "lembrete"}]
        matched = [row for row in candidates if any(word in _plain(row.get("title")) for word in words)] if words else candidates
        if len(matched) == 1:
            row = matched[0]
            return ActionDraft("update_obligation", {"record_id": int(row["id"]), "status": "Concluído", "previous_status": str(row.get("status") or "Pendente")}, (), f"Marcar “{row.get('title', 'obrigação')}” como concluído", "Busca local")

    if "concil" in plain and "nota" in plain:
        matches = smart_invoice_matches(transactions, invoices)
        number = re.search(r"(?i)nota(?:\s+fiscal)?\s+(?:n[ºo.]?\s+)?([A-Za-z0-9./_-]+)", question)
        if number and not matches.empty:
            selected = matches[matches["invoice_number"].astype(str).str.lower() == number.group(1).lower()]
            if len(selected) == 1:
                row = selected.iloc[0]
                tx = transactions[transactions["id"] == int(row["tx_id"])].iloc[0]
                payload = {"record_id": int(row["tx_id"]), "invoice_id": int(row["invoice_id"]), "document_number": str(row["invoice_number"]), "counterparty": str(row["customer"]), "previous_document_number": str(tx.get("document_number") or ""), "previous_counterparty": str(tx.get("counterparty") or ""), "score": int(row["score"]), "reasons": str(row["reasons"])}
                return ActionDraft("reconcile_invoice", payload, (), f"Conciliar nota {row['invoice_number']} com a receita de {_money(row['tx_value'])} · confiança {row['confidence']} ({row['score']}%)", "Conciliação inteligente")
    return None


def proactive_answer(*, transactions: pd.DataFrame, invoices: pd.DataFrame, obligations: list[dict], das_rows: list[dict], today: date | None = None) -> dict[str, str]:
    today = today or date.today()
    duplicates = duplicate_groups(transactions)
    matches = smart_invoice_matches(transactions, invoices)
    pending_obligations = [row for row in obligations if str(row.get("status") or "").lower() == "pendente"]
    pending_das = [row for row in das_rows if str(row.get("status") or "").lower() == "pendente"]
    items: list[str] = []
    if pending_das:
        items.append(f"{len(pending_das)} DAS pendente(s)")
    if pending_obligations:
        items.append(f"{len(pending_obligations)} prazo(s) ou lembrete(s) pendente(s)")
    if not matches.empty:
        items.append(f"{len(matches)} nota(s) com sugestão de conciliação")
    if not duplicates.empty:
        items.append(f"{len(duplicates)} lançamento(s) em possíveis duplicidades")
    raw = "Hoje eu priorizaria estes pontos:\n\n" + "\n".join(f"• {item}" for item in items) if items else "Seus dados não mostram pendências críticas ou duplicidades agora."
    answer = humanize_local_response(raw, question="Ver minhas prioridades", source="proactive")
    return {"answer": answer, "confidence": "Alta", "reason": f"Verificação local em DAS, obrigações, notas e movimentações em {today.strftime('%d/%m/%Y')}."}
