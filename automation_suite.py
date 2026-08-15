from __future__ import annotations

from datetime import date
from difflib import SequenceMatcher
from typing import Iterable
from urllib.parse import quote

import pandas as pd

from business_tools import monthly_closing
from fiscal_rules import das_status
from reconciliation_tools import smart_invoice_matches


def _date(value):
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, date):
        return value
    if value is not None:
        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None
    return None


def learned_category(description: str, tx_type: str, history: pd.DataFrame, fallback: str) -> dict:
    """Suggest a category from the user's own prior corrections, with a safe fallback."""
    text = " ".join(str(description or "").lower().split())
    if not text or history.empty or not {"description", "category"}.issubset(history.columns):
        return {"category": fallback, "confidence": "Baixa", "source": "regra padrão"}
    candidates = history.copy()
    if "tx_type" in candidates.columns:
        candidates = candidates[candidates["tx_type"].astype(str) == str(tx_type)]
    best = (0.0, fallback)
    for row in candidates.itertuples():
        previous = " ".join(str(getattr(row, "description", "") or "").lower().split())
        category = str(getattr(row, "category", "") or "").strip()
        if not previous or not category:
            continue
        similarity = SequenceMatcher(None, text, previous).ratio()
        if similarity > best[0]:
            best = (similarity, category)
    if best[0] >= 0.72:
        return {"category": best[1], "confidence": "Alta", "source": "seu histórico"}
    if best[0] >= 0.52:
        return {"category": best[1], "confidence": "Média", "source": "seu histórico"}
    return {"category": fallback, "confidence": "Baixa", "source": "regra padrão"}


def das_payment_matches(das_rows: Iterable[dict], transactions: pd.DataFrame) -> list[dict]:
    if transactions.empty:
        return []
    expenses = transactions[transactions["tx_type"] == "Despesa"].copy()
    matches = []
    for item in das_rows:
        if das_status(item.get("status", "Pendente"), item.get("due_date")) == "Pago":
            continue
        due = _date(item.get("due_date"))
        expected = float(item.get("amount") or 0)
        best = None
        for row in expenses.itertuples():
            tx_date = _date(getattr(row, "tx_date", None))
            description = str(getattr(row, "description", "") or "").lower()
            value = float(getattr(row, "value", 0) or 0)
            if not tx_date or not due or abs((tx_date - due).days) > 45:
                continue
            score = 0
            reasons = []
            if any(term in description for term in ("das", "pgmei", "simples nacional", "imposto mei")):
                score += 55; reasons.append("descrição compatível")
            if expected and abs(value - expected) <= max(0.02, expected * 0.01):
                score += 35; reasons.append("valor compatível")
            if abs((tx_date - due).days) <= 7:
                score += 10; reasons.append("data próxima")
            if best is None or score > best[0]:
                best = (score, row, reasons)
        if best and best[0] >= 55:
            row = best[1]
            matches.append({"competence": item.get("competence"), "das_id": item.get("id"), "transaction_id": int(row.id), "date": _date(row.tx_date), "value": float(row.value), "score": best[0], "reasons": ", ".join(best[2])})
    return sorted(matches, key=lambda item: item["score"], reverse=True)


def cash_forecast(transactions: pd.DataFrame, months: int = 3, today: date | None = None) -> pd.DataFrame:
    today = today or date.today()
    if transactions.empty:
        avg_revenue = avg_expense = opening = 0.0
    else:
        tx = transactions.copy()
        tx["tx_date"] = pd.to_datetime(tx["tx_date"], errors="coerce")
        recent_start = pd.Timestamp(today) - pd.DateOffset(months=3)
        recent = tx[tx["tx_date"] >= recent_start]
        avg_revenue = float(recent[recent["tx_type"] == "Receita"]["value"].sum()) / 3
        avg_expense = float(recent[recent["tx_type"] == "Despesa"]["value"].sum()) / 3
        opening = float(tx[tx["tx_type"] == "Receita"]["value"].sum() - tx[tx["tx_type"] == "Despesa"]["value"].sum())
    rows = []
    balance = opening
    for offset in range(1, max(1, months) + 1):
        target = pd.Timestamp(today) + pd.DateOffset(months=offset)
        balance += avg_revenue - avg_expense
        rows.append({"Mês": target.strftime("%m/%Y"), "Receitas previstas": avg_revenue, "Despesas previstas": avg_expense, "Saldo projetado": balance})
    return pd.DataFrame(rows)


def expense_anomalies(transactions: pd.DataFrame, year: int) -> list[dict]:
    if transactions.empty:
        return []
    tx = transactions.copy()
    tx["tx_date"] = pd.to_datetime(tx["tx_date"], errors="coerce")
    expenses = tx[(tx["tx_type"] == "Despesa") & (tx["tx_date"].dt.year == year)]
    rows = []
    for category, group in expenses.groupby("category", dropna=False):
        values = pd.to_numeric(group["value"], errors="coerce").dropna()
        if len(values) < 3:
            continue
        median = float(values.median())
        limit = max(median * 2.5, median + 100)
        for row in group[pd.to_numeric(group["value"], errors="coerce") > limit].itertuples():
            rows.append({"id": int(row.id), "description": row.description, "category": category or "Sem categoria", "value": float(row.value), "reference": median})
    return sorted(rows, key=lambda item: item["value"], reverse=True)


def document_queue(transactions: pd.DataFrame, documents: Iterable[dict], year: int) -> dict:
    if transactions.empty:
        missing = transactions
    else:
        tx = transactions.copy()
        tx["tx_date"] = pd.to_datetime(tx["tx_date"], errors="coerce")
        missing = tx[(tx["tx_date"].dt.year == year) & tx["document_number"].fillna("").astype(str).str.strip().eq("")]
    refs = {str(item.get("reference_month") or "").strip() for item in documents}
    refs.discard("")
    return {"missing_count": len(missing), "missing": missing, "covered_months": len(refs)}


def receivable_reminders(invoices: pd.DataFrame, transactions: pd.DataFrame) -> list[dict]:
    if invoices.empty:
        return []
    linked = set(transactions["document_number"].fillna("").astype(str).str.strip()) if not transactions.empty else set()
    reminders = []
    for row in invoices.itertuples():
        number = str(getattr(row, "number", "") or "").strip()
        if str(getattr(row, "status", "")) != "Emitida" or (number and number in linked):
            continue
        customer = str(getattr(row, "customer", "") or "cliente").strip()
        amount = float(getattr(row, "amount", 0) or 0)
        message = f"Olá, {customer}. Tudo bem? Estamos conferindo o pagamento da nota {number or 'fiscal'} no valor de R$ {amount:,.2f}. Se já foi pago, por favor desconsidere esta mensagem."
        reminders.append({"invoice_id": int(row.id), "customer": customer, "number": number, "amount": amount, "message": message, "whatsapp_url": "https://wa.me/?text=" + quote(message), "email_url": "mailto:?subject=" + quote(f"Pagamento da nota {number}") + "&body=" + quote(message)})
    return reminders


def automation_overview(profile: dict, transactions: pd.DataFrame, invoices: pd.DataFrame, das_rows: list[dict], obligations: list[dict], documents: list[dict], year: int, month: int) -> dict:
    closing = monthly_closing(transactions, invoices, documents, das_rows, year, month)
    invoice_matches = smart_invoice_matches(transactions, invoices)
    payment_matches = das_payment_matches(das_rows, transactions)
    anomalies = expense_anomalies(transactions, year)
    documents_status = document_queue(transactions, documents, year)
    reminders = receivable_reminders(invoices, transactions)
    overdue_das = sum(1 for item in das_rows if das_status(item.get("status", "Pendente"), item.get("due_date")) == "Atrasado")
    overdue_obligations = sum(1 for item in obligations if item.get("status") != "Concluído" and _date(item.get("due_date")) and _date(item.get("due_date")) < date.today())
    actions = []
    if closing["score"] < 100: actions.append(f"Fechamento de {month:02d}/{year} está {closing['score']}% pronto.")
    if not invoice_matches.empty: actions.append(f"Há {len(invoice_matches)} conciliação(ões) de nota sugerida(s).")
    if payment_matches: actions.append(f"Há {len(payment_matches)} possível(is) pagamento(s) de DAS no extrato.")
    if documents_status["missing_count"]: actions.append(f"Há {documents_status['missing_count']} lançamento(s) sem documento.")
    if overdue_das: actions.append(f"Há {overdue_das} DAS em atraso.")
    if overdue_obligations: actions.append(f"Há {overdue_obligations} obrigação(ões) vencida(s).")
    if anomalies: actions.append(f"Há {len(anomalies)} despesa(s) fora do padrão para revisar.")
    if reminders: actions.append(f"Há {len(reminders)} nota(s) sem recebimento conciliado.")
    if not actions: actions.append("Tudo em ordem: nenhuma ação importante identificada hoje.")
    return {"closing": closing, "invoice_matches": invoice_matches, "das_matches": payment_matches, "anomalies": anomalies, "documents": documents_status, "reminders": reminders, "actions": actions, "forecast": cash_forecast(transactions, 3)}

