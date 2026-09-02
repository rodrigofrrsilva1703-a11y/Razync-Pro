from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from business_tools import monthly_closing
from compact_cards import metric_card
from contextual_ai import contextual_ai_button
from fiscal_rules import das_status
from ui_system import alert_card, section
from table_ui import professional_table


def render_fiscal_workspace(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    current_year: int,
    annual_limit: float,
    annual_revenue: float,
    brl,
    navigate,
) -> None:
    """Integrated fiscal workspace for the core MEI routine."""
    today = date.today()
    overdue_das = [row for row in das_rows if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Atrasado"]
    pending_das = [row for row in das_rows if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Pendente"]
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

    st.markdown("### Fiscal MEI")
    st.caption("DAS, notas, obrigações e declaração anual reunidos em uma única rotina.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if metric_card("DAS em atraso", str(len(overdue_das)), key="fiscal_overdue_das", help_text="Abrir o controle do DAS"):
            navigate("DAS")
    with c2:
        if metric_card("DAS pendentes", str(len(pending_das)), key="fiscal_pending_das", help_text="Abrir o controle do DAS"):
            navigate("DAS")
    with c3:
        if metric_card("Notas emitidas", str(len(invoices)), key="fiscal_invoices", help_text="Abrir Notas Fiscais"):
            navigate("Notas Fiscais")
    with c4:
        if metric_card(
            "Limite usado",
            f"{(annual_revenue / annual_limit * 100) if annual_limit else 0:.1f}%",
            key="fiscal_limit",
            help_text="Abrir a declaração e o acompanhamento do faturamento",
        ):
            navigate("DASN-SIMEI")

    ai1, ai2, ai3 = st.columns(3)
    with ai1:
        contextual_ai_button(
            "Revisar rotina fiscal",
            key="fiscal_review",
            navigate=navigate,
            source="fiscal_workspace",
            title="Revisão fiscal do MEI",
            question="Revise minha situação fiscal atual no Razync e diga o que exige atenção primeiro. Considere DAS, obrigações, notas e faturamento.",
            detail=f"DAS atrasados: {len(overdue_das)}; DAS pendentes: {len(pending_das)}; obrigações vencidas: {len(overdue_obligations)}.",
            page="Fiscal",
        )
    with ai2:
        contextual_ai_button(
            "Entender limite do MEI",
            key="fiscal_limit_ai",
            navigate=navigate,
            source="fiscal_workspace",
            title="Limite anual do MEI",
            question="Explique quanto do meu limite anual do MEI já foi usado e o que devo acompanhar até o fim do ano. Use apenas meus dados cadastrados e deixe claro quando algo for estimativa.",
            detail=f"Faturamento no ano: {brl(annual_revenue)}; limite monitorado: {brl(annual_limit)}.",
            page="Fiscal",
        )
    with ai3:
        contextual_ai_button(
            "Preparar fechamento",
            key="fiscal_closing_ai",
            navigate=navigate,
            source="fiscal_workspace",
            title="Preparação do fechamento mensal",
            question="Revise o que falta para eu fechar este mês com documentos, notas, DAS e movimentações organizados.",
            detail=f"Documentos: {len(documents)}; notas: {len(invoices)}.",
            page="Fiscal",
        )

    if overdue_das:
        alert_card("danger", "DAS em atraso", f"Existem {len(overdue_das)} competência(s) vencida(s) para revisar.")
    elif overdue_obligations:
        alert_card("warn", "Obrigações vencidas", f"Existem {len(overdue_obligations)} tarefa(s) fiscal(is) vencida(s).")
    else:
        alert_card("ok", "Rotina fiscal sem alerta crítico", "Nenhum DAS atrasado ou obrigação manual vencida foi identificado.")

    section("Rotina fiscal", "Comece pela tarefa que corresponde ao que você precisa fazer agora.")
    a1, a2, a3, a4 = st.columns(4)
    if a1.button("DAS mensal", width="stretch"):
        navigate("DAS")
    if a2.button("Notas fiscais", width="stretch"):
        navigate("Notas Fiscais")
    if a3.button("Prazos e obrigações", width="stretch"):
        navigate("Obrigações")
    if a4.button("Declaração anual", width="stretch"):
        navigate("DASN-SIMEI")

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        section("Competências do DAS", "Situação das guias já controladas no Razync.")
        if not das_rows:
            st.info("Nenhuma competência do DAS foi cadastrada ainda.")
        else:
            rows = []
            for row in das_rows:
                rows.append({
                    "Competência": row.get("competence"),
                    "Vencimento": row.get("due_date"),
                    "Valor": float(row.get("amount") or 0),
                    "Situação": das_status(row.get("status", "Pendente"), row.get("due_date"), today),
                })
            professional_table(
                pd.DataFrame(rows).tail(12),
                max_visible_rows=8,
                column_config={
                    "Vencimento": st.column_config.DateColumn(format="DD/MM/YYYY"),
                    "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
                },
            )
            if st.button("Abrir controle completo do DAS", key="fiscal_open_das", width="stretch"):
                navigate("DAS")

    with right:
        section("Fechamento atual", "Resumo do mês para saber se a documentação está organizada.")
        closing = monthly_closing(transactions, invoices, documents, das_rows, today.year, today.month)
        if metric_card("Organização do mês", f"{closing['score']}%", key="fiscal_closing", help_text="Abrir fechamento mensal"):
            navigate("Fechamento Mensal")
        st.progress(closing["score"] / 100)
        pending = [item for item in closing["checklist"] if not item["OK"]]
        if pending:
            for item in pending[:3]:
                st.caption(f"• {item['Item']}: {item['Detalhe']}")
            if st.button("Abrir fechamento mensal", width="stretch"):
                navigate("Fechamento Mensal")
        else:
            st.success("Fechamento do mês sem pendências no checklist.")

    with st.expander("Notas, documentos e relatórios"):
        n1, n2, n3 = st.columns(3)
        with n1:
            if metric_card("Notas cadastradas", str(len(invoices)), key="fiscal_notes_total", help_text="Abrir Notas Fiscais"):
                navigate("Notas Fiscais")
        with n2:
            if metric_card("Documentos armazenados", str(len(documents)), key="fiscal_documents", help_text="Abrir Documentos"):
                navigate("Documentos")
        with n3:
            if metric_card("Faturamento no ano", brl(annual_revenue), key="fiscal_revenue", help_text="Abrir relatório mensal"):
                navigate("Relatório Mensal")

        q1, q2, q3 = st.columns(3)
        if q1.button("Importar NFS-e", width="stretch"):
            navigate("Importar NFS-e")
        if q2.button("Relatório mensal", width="stretch"):
            navigate("Relatório Mensal")
        if q3.button("Documentos", width="stretch"):
            navigate("Documentos")

    with st.expander("Mais recursos fiscais"):
        st.caption("Use estas ferramentas quando precisar de uma conferência mais detalhada.")
        b1, b2 = st.columns(2)
        if b1.button("Fechamento mensal completo", width="stretch"):
            navigate("Fechamento Mensal")
        if b2.button("Espaço do contador", width="stretch"):
            navigate("Espaço do Contador")
