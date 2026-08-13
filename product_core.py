from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

from fiscal_rules import das_status

NAV_GROUPS = {
    "Visão Geral": ["Dashboard"],
    "Financeiro": ["Movimentações", "Importar Extrato", "Conciliação", "Fluxo de Caixa", "Análise Financeira"],
    "Fiscal MEI": ["Central Fiscal", "Fechamento Mensal", "Relatório Mensal", "Notas Fiscais", "DAS", "DASN-SIMEI", "Obrigações"],
    "Gestão": ["Clientes e Fornecedores", "Empregado", "Documentos"],
    "Relatórios": ["Central de Relatórios", "Assistente Razync"],
    "Configurações": ["Primeiros Passos", "Meu MEI", "Status do Sistema", "Backup"],
}


def group_for_page(page: str) -> str:
    for group, pages in NAV_GROUPS.items():
        if page in pages:
            return group
    return "Visão Geral"


def action_items(
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: Iterable[dict],
    obligations: Iterable[dict],
    annual_limit: float,
    annual_revenue: float,
) -> list[dict]:
    items: list[dict] = []
    today = date.today()

    if not profile.get("cnpj") or not profile.get("main_activity"):
        items.append({"priority": 1, "title": "Complete o cadastro do MEI", "detail": "CNPJ e atividade principal são usados nos relatórios e alertas.", "page": "Meu MEI"})

    overdue_das = []
    for row in das_rows:
        if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Atrasado":
            overdue_das.append(row)
    if overdue_das:
        items.append({"priority": 1, "title": f"{len(overdue_das)} DAS em atraso", "detail": "Revise as competências vencidas e registre os pagamentos.", "page": "DAS"})

    if annual_limit and annual_revenue / annual_limit >= 0.80:
        pct = annual_revenue / annual_limit * 100
        items.append({"priority": 1 if pct >= 90 else 2, "title": "Atenção ao limite do MEI", "detail": f"O faturamento registrado já representa {pct:.1f}% do limite monitorado.", "page": "Central Fiscal"})

    if not invoices.empty:
        documented = set(transactions.get("document_number", pd.Series(dtype=str)).fillna("").astype(str)) if not transactions.empty else set()
        active = invoices[invoices["status"] == "Emitida"] if "status" in invoices else invoices
        pending = active[~active["number"].fillna("").astype(str).isin(documented)] if "number" in active else active.iloc[0:0]
        if not pending.empty:
            items.append({"priority": 2, "title": f"{len(pending)} nota(s) sem conciliação", "detail": "Relacione as notas emitidas às receitas correspondentes.", "page": "Conciliação"})

    overdue_obligations = []
    for row in obligations:
        due = row.get("due_date")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due)
            except ValueError:
                due = None
        if row.get("status") != "Concluído" and due and due < today:
            overdue_obligations.append(row)
    if overdue_obligations:
        items.append({"priority": 2, "title": f"{len(overdue_obligations)} obrigação(ões) vencida(s)", "detail": "Atualize as tarefas vencidas da agenda.", "page": "Obrigações"})

    if transactions.empty:
        items.append({"priority": 3, "title": "Registre a primeira movimentação", "detail": "Receitas e despesas alimentam todos os relatórios do Razync Pro.", "page": "Movimentações"})

    if not items:
        items.append({"priority": 4, "title": "Tudo em ordem", "detail": "Nenhuma pendência importante foi identificada com os dados cadastrados.", "page": "Dashboard"})

    return sorted(items, key=lambda x: x["priority"])


def reconciliation_summary(transactions: pd.DataFrame, invoices: pd.DataFrame) -> dict:
    if transactions.empty:
        tx_docs = set()
    else:
        tx_docs = set(transactions["document_number"].fillna("").astype(str).str.strip())
        tx_docs.discard("")

    if invoices.empty:
        emitted = invoices
    else:
        emitted = invoices[invoices["status"] == "Emitida"] if "status" in invoices.columns else invoices

    invoice_rows = []
    if not emitted.empty:
        for _, row in emitted.iterrows():
            number = str(row.get("number") or "").strip()
            reconciled = bool(number and number in tx_docs)
            invoice_rows.append({
                "ID": row.get("id"),
                "Data": row.get("issue_date"),
                "Nota": number,
                "Cliente": row.get("customer", ""),
                "Valor": float(row.get("amount") or 0),
                "Conciliada": reconciled,
            })

    duplicated = 0
    if not transactions.empty:
        temp = transactions.copy()
        temp["_desc"] = temp["description"].fillna("").astype(str).str.lower().str.strip()
        duplicated = int(temp.duplicated(subset=["tx_date", "tx_type", "value", "_desc"], keep=False).sum())

    detail = pd.DataFrame(invoice_rows)
    pending = detail[~detail["Conciliada"]].copy() if not detail.empty else detail
    return {
        "total_invoices": len(detail),
        "reconciled_invoices": int(detail["Conciliada"].sum()) if not detail.empty else 0,
        "pending_invoices": pending,
        "possible_duplicate_transactions": duplicated,
    }


def assistant_answer(
    question: str,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    annual_limit: float,
    year: int,
) -> str:
    q = (question or "").lower().strip()
    if transactions.empty:
        year_tx = transactions
    else:
        year_tx = transactions[transactions["tx_date"].dt.year == year]
    revenue = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
    expense = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0
    result = revenue - expense

    def money(v: float) -> str:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    if "limite" in q or "quanto posso faturar" in q:
        remaining = max(annual_limit - revenue, 0)
        return f"Em {year}, o Razync Pro tem {money(revenue)} de receita registrada. O limite monitorado é {money(annual_limit)} e restam {money(remaining)}."
    if "lucro" in q or "resultado" in q or "sobrou" in q:
        return f"O resultado estimado de {year} é {money(result)}: {money(revenue)} de receitas menos {money(expense)} de despesas registradas."
    if "despesa" in q or "gasto" in q:
        if year_tx.empty:
            return f"Ainda não há despesas registradas em {year}."
        d = year_tx[year_tx["tx_type"] == "Despesa"]
        if d.empty:
            return f"Ainda não há despesas registradas em {year}."
        top = d.groupby("category")["value"].sum().sort_values(ascending=False).head(3)
        parts = [f"{idx}: {money(val)}" for idx, val in top.items()]
        return f"As despesas registradas em {year} somam {money(expense)}. Maiores categorias: " + "; ".join(parts) + "."
    if "das" in q:
        overdue = [r for r in das_rows if das_status(r.get("status", "Pendente"), r.get("due_date")) == "Atrasado"]
        pending = [r for r in das_rows if das_status(r.get("status", "Pendente"), r.get("due_date")) == "Pendente"]
        return f"O controle atual mostra {len(overdue)} DAS em atraso e {len(pending)} pendente(s)."
    if "nota" in q or "nf" in q:
        rec = reconciliation_summary(transactions, invoices)
        return f"Existem {rec['total_invoices']} nota(s) emitida(s) cadastrada(s), sendo {rec['reconciled_invoices']} conciliada(s) com receitas e {len(rec['pending_invoices'])} pendente(s)."
    if "fatur" in q or "receita" in q:
        return f"A receita registrada em {year} é {money(revenue)}."
    return "Posso analisar faturamento, limite do MEI, despesas, resultado, DAS e conciliação de notas usando os dados cadastrados no Razync Pro."

# trigger product restructure
