from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd

from fiscal_rules import das_status

NAV_GROUPS = {
    "Visão Geral": ["Dashboard", "Produtividade", "Conta e Sistema", "Central de Automações", "Assistente Razync"],
    "Financeiro": ["Financeiro", "Movimentações", "Recorrências", "Importar Extrato", "Conciliação", "Fluxo de Caixa", "Análise Financeira"],
    "Fiscal MEI": ["Fiscal", "DAS", "DASN-SIMEI", "Obrigações", "Notas Fiscais", "Importar NFS-e", "Relatório Mensal", "Fechamento Mensal"],
    "Gestão": ["Clientes e Fornecedores", "Empregado", "Documentos", "Espaço do Contador"],
    "Configurações": ["Primeiros Passos", "Meu MEI", "Central de Notificações", "Integrações", "Plano e Assinatura", "Segurança da Conta", "Histórico de Atividades", "Status do Sistema", "Backup"],
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
        items.append({"priority": 1 if pct >= 90 else 2, "title": "Atenção ao limite do MEI", "detail": f"O faturamento registrado já representa {pct:.1f}% do limite monitorado.", "page": "Análise Financeira"})

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
        emitted = invoices[invoices["status"] == "Emitida"] if "status" in invoices else invoices
    if emitted.empty:
        pending = emitted
    else:
        pending = emitted[~emitted["number"].fillna("").astype(str).str.strip().isin(tx_docs)]
    return {
        "total_invoices": len(emitted),
        "reconciled_invoices": len(emitted) - len(pending),
        "pending_invoices": pending,
    }


def assistant_answer(question: str, transactions: pd.DataFrame, invoices: pd.DataFrame, das_rows: Iterable[dict], annual_limit: float, current_year: int, obligations: Iterable[dict] = (), documents: Iterable[dict] = ()) -> str:
    question = (question or "").lower().strip()
    year_tx = transactions[transactions["tx_date"].dt.year == current_year] if not transactions.empty else transactions
    revenue = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
    expense = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0
    if "quanto" in question and ("fatur" in question or "limite" in question):
        remaining = max(0.0, float(annual_limit or 0) - revenue)
        return f"Neste ano há R$ {remaining:,.2f} de limite monitorado disponível com base nos registros atuais.".replace(",", "X").replace(".", ",").replace("X", ".")
    if "maior despesa" in question and not year_tx.empty:
        expenses = year_tx[year_tx["tx_type"] == "Despesa"]
        if not expenses.empty:
            row = expenses.loc[expenses["value"].idxmax()]
            return f"A maior despesa registrada no ano é {row['description']}, no valor de R$ {float(row['value']):,.2f}.".replace(",", "X").replace(".", ",").replace("X", ".")
    if "das" in question:
        overdue = [row for row in das_rows if das_status(row.get("status", "Pendente"), row.get("due_date")) == "Atrasado"]
        return "Não há DAS em atraso nos registros atuais." if not overdue else f"Há {len(overdue)} competência(s) de DAS em atraso nos registros atuais."
    if "document" in question:
        return f"Há {len(list(documents))} documento(s) armazenado(s) atualmente."
    if "nota" in question:
        return f"Há {len(invoices)} nota(s) fiscal(is) cadastrada(s)."
    if "trimestre" in question:
        if year_tx.empty:
            return "Ainda não há movimentações suficientes para calcular o trimestre."
        latest_month = int(year_tx["tx_date"].dt.month.max())
        quarter = (latest_month - 1) // 3 + 1
        start = (quarter - 1) * 3 + 1
        quarter_rows = year_tx[(year_tx["tx_date"].dt.month >= start) & (year_tx["tx_date"].dt.month <= start + 2) & (year_tx["tx_type"] == "Receita")]
        value = float(quarter_rows["value"].sum()) if not quarter_rows.empty else 0.0
        return f"O faturamento registrado no {quarter}º trimestre é R$ {value:,.2f}.".replace(",", "X").replace(".", ",").replace("X", ".")
    result = revenue - expense
    return f"No ano atual, os registros mostram R$ {revenue:,.2f} de receitas, R$ {expense:,.2f} de despesas e resultado de R$ {result:,.2f}.".replace(",", "X").replace(".", ",").replace("X", ".")
