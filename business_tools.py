from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

from fiscal_rules import das_status


def month_slice(transactions: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    if transactions.empty:
        return transactions.copy()
    return transactions[(transactions["tx_date"].dt.year == year) & (transactions["tx_date"].dt.month == month)].copy()


def monthly_closing(transactions: pd.DataFrame, invoices: pd.DataFrame, documents: list[dict], das_rows: list[dict], year: int, month: int) -> dict:
    tx = month_slice(transactions, year, month)
    revenue = float(tx[tx["tx_type"] == "Receita"]["value"].sum()) if not tx.empty else 0.0
    expenses = float(tx[tx["tx_type"] == "Despesa"]["value"].sum()) if not tx.empty else 0.0
    result = revenue - expenses

    month_key = f"{year}-{month:02d}"
    das = next((d for d in das_rows if str(d.get("competence")) == month_key), None)
    das_current = das_status(das.get("status", "Pendente"), das.get("due_date")) if das else "Não criado"

    if invoices.empty:
        invoice_total = 0.0
        invoice_count = 0
    else:
        inv = invoices[(invoices["issue_date"].dt.year == year) & (invoices["issue_date"].dt.month == month) & (invoices["status"] == "Emitida")]
        invoice_total = float(inv["amount"].sum()) if not inv.empty else 0.0
        invoice_count = len(inv)

    docs_month = [d for d in documents if str(d.get("reference_month") or "").strip() == month_key]
    missing_doc_tx = 0
    if not tx.empty:
        missing_doc_tx = int(tx["document_number"].fillna("").astype(str).str.strip().eq("").sum())

    checklist = [
        {"Item": "Movimentações do mês revisadas", "OK": not tx.empty, "Detalhe": f"{len(tx)} lançamento(s)"},
        {"Item": "Receitas registradas", "OK": revenue > 0, "Detalhe": f"R$ {revenue:,.2f}"},
        {"Item": "DAS da competência criado", "OK": das is not None, "Detalhe": das_current},
        {"Item": "Documentos da competência armazenados", "OK": len(docs_month) > 0, "Detalhe": f"{len(docs_month)} documento(s)"},
        {"Item": "Lançamentos com documento informado", "OK": missing_doc_tx == 0, "Detalhe": f"{missing_doc_tx} sem documento"},
        {"Item": "Notas fiscais conferidas", "OK": invoice_count > 0 or revenue == 0, "Detalhe": f"{invoice_count} nota(s) • R$ {invoice_total:,.2f}"},
    ]

    score = round(sum(1 for item in checklist if item["OK"]) / len(checklist) * 100)
    difference = revenue - invoice_total

    return {
        "revenue": revenue,
        "expense": expenses,
        "expenses": expenses,
        "result": result,
        "invoice_total": invoice_total,
        "invoice_count": invoice_count,
        "das_status": das_current,
        "documents_count": len(docs_month),
        "missing_document_transactions": missing_doc_tx,
        "invoice_difference": difference,
        "score": score,
        "checklist": checklist,
        "transactions": tx,
    }


def financial_analysis(transactions: pd.DataFrame, year: int) -> dict:
    if transactions.empty:
        empty = pd.DataFrame(columns=["Categoria", "Valor"])
        return {"revenue": 0.0, "expense": 0.0, "result": 0.0, "margin": 0.0, "expense_categories": empty, "monthly": pd.DataFrame()}

    cur = transactions[transactions["tx_date"].dt.year == year].copy()
    revenue = float(cur[cur["tx_type"] == "Receita"]["value"].sum())
    expenses = float(cur[cur["tx_type"] == "Despesa"]["value"].sum())
    result = revenue - expenses
    margin = (result / revenue * 100) if revenue else 0.0

    exp = cur[cur["tx_type"] == "Despesa"].groupby("category", dropna=False)["value"].sum().sort_values(ascending=False).reset_index()
    exp.columns = ["Categoria", "Valor"]

    monthly_rows = []
    for month in range(1, 13):
        part = cur[cur["tx_date"].dt.month == month]
        ent = float(part[part["tx_type"] == "Receita"]["value"].sum()) if not part.empty else 0.0
        sai = float(part[part["tx_type"] == "Despesa"]["value"].sum()) if not part.empty else 0.0
        monthly_rows.append({"Mês": month, "Receitas": ent, "Despesas": sai, "Resultado": ent-sai})

    return {
        "revenue": revenue,
        "expense": expenses,
        "expenses": expenses,
        "result": result,
        "margin": margin,
        "expense_categories": exp,
        "monthly": pd.DataFrame(monthly_rows),
    }


def consistency_checks(transactions: pd.DataFrame, invoices: pd.DataFrame, das_rows: Iterable[dict]) -> list[dict]:
    checks: list[dict] = []
    if not transactions.empty:
        duplicated = transactions.duplicated(subset=["tx_date", "tx_type", "description", "value"], keep=False)
        count_dup = int(duplicated.sum())
        if count_dup:
            checks.append({"Nível": "Atenção", "Verificação": "Possíveis lançamentos duplicados", "Quantidade": count_dup})
        no_doc = int(transactions["document_number"].fillna("").astype(str).str.strip().eq("").sum())
        if no_doc:
            checks.append({"Nível": "Informação", "Verificação": "Lançamentos sem documento informado", "Quantidade": no_doc})

    if not invoices.empty and not transactions.empty:
        documented = set(transactions["document_number"].fillna("").astype(str).str.strip())
        active = invoices[invoices["status"] == "Emitida"]
        unreconciled = int((~active["number"].fillna("").astype(str).str.strip().isin(documented)).sum())
        if unreconciled:
            checks.append({"Nível": "Atenção", "Verificação": "Notas emitidas sem receita conciliada", "Quantidade": unreconciled})

    overdue = sum(1 for d in das_rows if das_status(d.get("status", "Pendente"), d.get("due_date")) == "Atrasado")
    if overdue:
        checks.append({"Nível": "Crítico", "Verificação": "DAS em atraso", "Quantidade": overdue})

    if not checks:
        checks.append({"Nível": "OK", "Verificação": "Nenhuma inconsistência básica identificada", "Quantidade": 0})
    return checks
