from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Iterable

import pandas as pd


def next_recurrence_date(current: date, frequency: str) -> date:
    if frequency == "Semanal":
        return current + timedelta(days=7)
    if frequency == "Anual":
        last_day = calendar.monthrange(current.year + 1, current.month)[1]
        return date(current.year + 1, current.month, min(current.day, last_day))
    if frequency == "Mensal":
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, min(current.day, last_day))
    raise ValueError("Frequência inválida.")


def financial_projection(
    transactions: pd.DataFrame,
    annual_limit: float,
    year: int,
    today: date | None = None,
) -> dict:
    today = today or date.today()
    if transactions.empty:
        revenue = expense = 0.0
    else:
        current = transactions[transactions["tx_date"].dt.year == year]
        revenue = float(current[current["tx_type"] == "Receita"]["value"].sum()) if not current.empty else 0.0
        expense = float(current[current["tx_type"] == "Despesa"]["value"].sum()) if not current.empty else 0.0

    elapsed_months = today.month if today.year == year else (12 if year < today.year else 1)
    projected_revenue = revenue / max(elapsed_months, 1) * 12
    projected_expense = expense / max(elapsed_months, 1) * 12
    projected_result = projected_revenue - projected_expense
    projected_limit_pct = projected_revenue / annual_limit * 100 if annual_limit else 0.0
    return {
        "revenue": revenue,
        "expense": expense,
        "projected_revenue": projected_revenue,
        "projected_expense": projected_expense,
        "projected_result": projected_result,
        "projected_limit_pct": projected_limit_pct,
        "limit_risk": projected_limit_pct >= 90,
    }


def upcoming_deadlines(
    das_rows: Iterable[dict],
    obligations: Iterable[dict],
    today: date | None = None,
    days: int = 30,
) -> list[dict]:
    today = today or date.today()
    limit = today + timedelta(days=max(days, 0))
    rows: list[dict] = []

    for item in das_rows:
        due = item.get("due_date")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due[:10])
            except ValueError:
                due = None
        status = str(item.get("status") or "Pendente")
        if due and today <= due <= limit and status not in {"Pago", "Concluído"}:
            rows.append({
                "date": due,
                "title": f"DAS {item.get('competence') or ''}".strip(),
                "status": status,
                "page": "DAS",
            })

    for item in obligations:
        due = item.get("due_date")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due[:10])
            except ValueError:
                due = None
        status = str(item.get("status") or "Pendente")
        if due and today <= due <= limit and status != "Concluído":
            rows.append({
                "date": due,
                "title": str(item.get("title") or "Obrigação"),
                "status": status,
                "page": "Obrigações",
            })

    return sorted(rows, key=lambda item: (item["date"], item["title"]))
