from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Iterable

import pandas as pd
from openai import OpenAI


DEFAULT_MODEL = "gpt-5.6-luna"


class RazyncAIError(RuntimeError):
    """Raised when the external AI provider cannot answer safely."""


def _date_value(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _money(value: float) -> float:
    return round(float(value or 0.0), 2)


def build_safe_business_context(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: Iterable[dict],
    obligations: Iterable[dict],
    documents: Iterable[dict],
    annual_limit: float,
    year: int,
    today: date | None = None,
) -> dict:
    """Build an aggregate-only context without direct personal identifiers."""
    today = today or date.today()
    tx = transactions.copy()
    if tx.empty:
        year_tx = tx
    else:
        dates = pd.to_datetime(tx["tx_date"], errors="coerce")
        tx = tx.assign(tx_date=dates)
        year_tx = tx[tx["tx_date"].dt.year == year]

    revenue_rows = year_tx[year_tx["tx_type"] == "Receita"] if not year_tx.empty else year_tx
    expense_rows = year_tx[year_tx["tx_type"] == "Despesa"] if not year_tx.empty else year_tx
    revenue = _money(revenue_rows["value"].sum()) if not revenue_rows.empty else 0.0
    expense = _money(expense_rows["value"].sum()) if not expense_rows.empty else 0.0

    monthly: list[dict] = []
    for month in range(1, 13):
        if year_tx.empty:
            month_rows = year_tx
        else:
            month_rows = year_tx[year_tx["tx_date"].dt.month == month]
        monthly.append(
            {
                "month": month,
                "revenue": _money(month_rows[month_rows["tx_type"] == "Receita"]["value"].sum()) if not month_rows.empty else 0.0,
                "expense": _money(month_rows[month_rows["tx_type"] == "Despesa"]["value"].sum()) if not month_rows.empty else 0.0,
            }
        )

    def category_totals(frame: pd.DataFrame) -> list[dict]:
        if frame.empty or "category" not in frame.columns:
            return []
        grouped = frame.assign(category=frame["category"].fillna("Outros").astype(str))
        totals = grouped.groupby("category")["value"].sum().sort_values(ascending=False).head(8)
        return [{"category": str(name), "value": _money(value)} for name, value in totals.items()]

    largest_expense = None
    if not expense_rows.empty:
        row = expense_rows.loc[expense_rows["value"].astype(float).idxmax()]
        largest_expense = {
            "date": row["tx_date"].date().isoformat() if hasattr(row["tx_date"], "date") else str(row["tx_date"]),
            "category": str(row.get("category") or "Outros"),
            "value": _money(row.get("value") or 0),
        }

    invoice_rows = invoices.copy()
    if invoice_rows.empty:
        emitted_count = cancelled_count = 0
        invoice_total = 0.0
    else:
        statuses = invoice_rows.get("status", pd.Series(index=invoice_rows.index, dtype=str)).fillna("Emitida").astype(str)
        emitted = invoice_rows[statuses == "Emitida"]
        emitted_count = int(len(emitted))
        cancelled_count = int((statuses == "Cancelada").sum())
        invoice_total = _money(emitted["amount"].sum()) if "amount" in emitted else 0.0

    tx_docs = set()
    if not year_tx.empty and "document_number" in year_tx.columns:
        tx_docs = set(year_tx["document_number"].fillna("").astype(str).str.strip())
        tx_docs.discard("")
    unreconciled_invoices = 0
    if not invoice_rows.empty and "number" in invoice_rows.columns:
        active = invoice_rows[invoice_rows.get("status", "Emitida") == "Emitida"] if "status" in invoice_rows.columns else invoice_rows
        numbers = active["number"].fillna("").astype(str).str.strip()
        unreconciled_invoices = int((~numbers.isin(tx_docs)).sum())

    das_counter = Counter()
    next_das_due = None
    for item in das_rows:
        status = str(item.get("status") or "Pendente")
        due = _date_value(item.get("due_date"))
        if status == "Pago":
            das_counter["paid"] += 1
        elif due and due < today:
            das_counter["overdue"] += 1
        else:
            das_counter["pending"] += 1
            if due and (next_das_due is None or due < next_das_due):
                next_das_due = due

    obligation_counter = Counter()
    next_obligation_due = None
    for item in obligations:
        if str(item.get("status") or "") == "Concluído":
            obligation_counter["done"] += 1
            continue
        due = _date_value(item.get("due_date"))
        if due and due < today:
            obligation_counter["overdue"] += 1
        else:
            obligation_counter["pending"] += 1
            if due and (next_obligation_due is None or due < next_obligation_due):
                next_obligation_due = due

    document_categories = Counter(str(item.get("category") or "Outros") for item in documents)
    missing_document_numbers = 0
    if not year_tx.empty and "document_number" in year_tx.columns:
        missing_document_numbers = int(year_tx["document_number"].fillna("").astype(str).str.strip().eq("").sum())

    opening = _date_value(profile.get("opening_date"))
    remaining = max(float(annual_limit or 0) - revenue, 0.0)
    limit_usage = (revenue / float(annual_limit) * 100.0) if annual_limit else 0.0

    return {
        "reference_date": today.isoformat(),
        "reference_year": year,
        "business": {
            "activity_type": str(profile.get("activity_type") or "Não informado"),
            "opening_year": opening.year if opening else None,
            "has_employee": bool(profile.get("has_employee", False)),
        },
        "financial": {
            "revenue": revenue,
            "expense": expense,
            "result": _money(revenue - expense),
            "annual_limit": _money(annual_limit),
            "remaining_limit": _money(remaining),
            "limit_usage_percent": round(limit_usage, 2),
            "revenue_by_category": category_totals(revenue_rows),
            "expense_by_category": category_totals(expense_rows),
            "largest_expense": largest_expense,
            "monthly": monthly,
            "transactions_count": int(len(year_tx)),
            "transactions_without_document_number": missing_document_numbers,
        },
        "fiscal": {
            "invoices_emitted": emitted_count,
            "invoices_cancelled": cancelled_count,
            "invoice_total": invoice_total,
            "invoices_unreconciled": unreconciled_invoices,
            "das_paid": das_counter["paid"],
            "das_pending": das_counter["pending"],
            "das_overdue": das_counter["overdue"],
            "next_das_due": next_das_due.isoformat() if next_das_due else None,
            "obligations_pending": obligation_counter["pending"],
            "obligations_overdue": obligation_counter["overdue"],
            "next_obligation_due": next_obligation_due.isoformat() if next_obligation_due else None,
        },
        "documents": {
            "count": int(sum(document_categories.values())),
            "by_category": dict(document_categories),
        },
        "privacy": {
            "direct_identifiers_included": False,
            "raw_documents_included": False,
            "transaction_descriptions_included": False,
            "counterparties_included": False,
        },
    }


INSTRUCTIONS = """
Você é o Assistente Razync, uma IA integrada a um sistema de organização financeira e fiscal para MEI no Brasil.
Responda em português do Brasil, com linguagem simples, objetiva e útil.
Use SOMENTE os dados agregados fornecidos no contexto do Razync para afirmar valores, quantidades, datas e situações do usuário.
Nunca invente lançamentos, documentos, clientes, CNPJ, CPF, pagamentos, prazos ou ações que não estejam no contexto.
Diferencie claramente dados registrados, estimativas e sugestões.
Você pode explicar conceitos gerais de organização financeira e fiscal, mas não deve afirmar que substitui contador, advogado ou portal oficial.
Para legislação, alíquotas, regras ou prazos que possam mudar e não estejam no contexto, oriente a confirmação em fonte oficial ou com profissional responsável.
Não diga que enviou, pagou, declarou, emitiu, alterou ou excluiu algo: você é somente consultivo nesta versão.
Não peça senha, token, CPF, CNPJ, dados bancários completos ou credenciais gov.br.
Se os dados forem insuficientes, diga exatamente o que está faltando no Razync.
Prefira respostas curtas, com no máximo 3 parágrafos ou poucos tópicos quando isso facilitar a leitura.
""".strip()


def ask_razync_ai(
    question: str,
    *,
    context: dict,
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> str:
    if not question or not question.strip():
        raise ValueError("A pergunta não pode ficar vazia.")
    if not api_key or not api_key.strip():
        raise RazyncAIError("OPENAI_API_KEY não configurada.")

    payload = (
        "Pergunta do usuário:\n"
        + question.strip()
        + "\n\nContexto agregado e autorizado do Razync (JSON):\n"
        + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    )
    try:
        client = OpenAI(api_key=api_key.strip(), timeout=25.0, max_retries=1)
        response = client.responses.create(
            model=(model or DEFAULT_MODEL).strip(),
            instructions=INSTRUCTIONS,
            input=payload,
            store=False,
            max_output_tokens=700,
        )
        answer = (response.output_text or "").strip()
    except Exception as exc:  # provider/network errors are converted to one safe app error
        raise RazyncAIError("A IA está temporariamente indisponível.") from exc
    if not answer:
        raise RazyncAIError("A IA não retornou uma resposta utilizável.")
    return answer
