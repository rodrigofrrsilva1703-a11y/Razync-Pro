from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from business_tools import monthly_closing
from compact_cards import stat_card
from contextual_ai import contextual_ai_button
from fiscal_rules import das_status
from mei_obligations import upcoming_automatic_obligations
from fiscal_timeline import build_fiscal_timeline, render_fiscal_timeline
from table_ui import professional_table
from ui_system import alert_card, section


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
    """Fiscal workspace organized around urgency and recurring MEI tasks."""
    today = date.today()
    overdue_das = [
        row for row in das_rows
        if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Atrasado"
    ]
    pending_das = [
        row for row in das_rows
        if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Pendente"
    ]
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

    limit_pct = (annual_revenue / annual_limit * 100) if annual_limit else 0.0

    raw_opening = profile.get("opening_date")
    if isinstance(raw_opening, str):
        try:
            raw_opening = date.fromisoformat(raw_opening[:10])
        except ValueError:
            raw_opening = None
    opening_date = raw_opening if isinstance(raw_opening, date) else None
    automatic_upcoming = upcoming_automatic_obligations(
        current_year,
        opening_date,
        das_rows,
        today=today,
        days_ahead=90,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("DAS em atraso", str(len(overdue_das)), tone="danger" if overdue_das else "neutral")
    with c2:
        stat_card("DAS pendentes", str(len(pending_das)), tone="warning" if pending_das else "neutral")
    with c3:
        stat_card("Notas cadastradas", str(len(invoices)))
    with c4:
        stat_card("Limite usado", f"{limit_pct:.1f}%", tone="warning" if limit_pct >= 80 else "neutral")

    if overdue_das:
        alert_card("danger", "DAS em atraso", f"Existem {len(overdue_das)} competência(s) vencida(s) para revisar.")
    elif overdue_obligations:
        alert_card("warn", "Obrigações vencidas", f"Existem {len(overdue_obligations)} tarefa(s) fiscal(is) vencida(s).")
    else:
        alert_card("ok", "Rotina fiscal em ordem", "Nenhum DAS atrasado ou obrigação manual vencida foi identificado.")

    a1, a2, spacer = st.columns([1, 1, 2.1], gap="small")
    if a1.button("DAS mensal", type="primary", width="stretch"):
        navigate("DAS")
    if a2.button("Notas fiscais", width="stretch"):
        navigate("Notas Fiscais")

    with st.expander("Outras rotinas fiscais"):
        x1, x2, x3 = st.columns(3)
        if x1.button("Prazos e obrigações", width="stretch"):
            navigate("Obrigações")
        if x2.button("Declaração anual", width="stretch"):
            navigate("DASN-SIMEI")
        if x3.button("Relatório mensal", width="stretch"):
            navigate("Relatório Mensal")

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        section("Competências do DAS", "Situação das guias já controladas.")
        if not das_rows:
            st.info("Nenhuma competência do DAS foi cadastrada ainda.")
        else:
            rows = [
                {
                    "Competência": row.get("competence"),
                    "Vencimento": row.get("due_date"),
                    "Valor": float(row.get("amount") or 0),
                    "Situação": das_status(
                        row.get("status", "Pendente"),
                        row.get("due_date"),
                        today,
                    ),
                }
                for row in das_rows
            ]
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
        section("Fechamento atual", "Veja rapidamente se o mês está organizado.")
        closing = monthly_closing(
            transactions, invoices, documents, das_rows, today.year, today.month
        )
        stat_card("Organização do mês", f"{closing['score']}%", detail="Checklist interno do Razync")
        st.progress(closing["score"] / 100)
        pending = [item for item in closing["checklist"] if not item["OK"]]
        if pending:
            for item in pending[:3]:
                st.caption(f"• {item['Item']}: {item['Detalhe']}")
            if st.button("Resolver fechamento", width="stretch"):
                navigate("Fechamento Mensal")
        else:
            st.success("Fechamento do mês sem pendências no checklist.")

    with st.expander("Linha do tempo fiscal", expanded=bool(overdue_das or overdue_obligations)):
        st.caption("DAS e obrigações organizados por urgência e vencimento.")
        timeline_items = build_fiscal_timeline(
            das_rows=das_rows,
            obligations=[*obligations, *automatic_upcoming],
            today=today,
            days_ahead=90,
        )
        render_fiscal_timeline(items=timeline_items, navigate=navigate)

    with st.expander("Analisar com Razync IA"):
        st.caption("Peça uma leitura dos dados fiscais sem alterar nenhuma informação.")
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

    with st.expander("Notas, documentos e relatórios"):
        n1, n2, n3 = st.columns(3)
        with n1:
            stat_card("Notas cadastradas", str(len(invoices)))
        with n2:
            stat_card("Documentos", str(len(documents)))
        with n3:
            stat_card("Faturamento no ano", brl(annual_revenue))

        q1, q2 = st.columns(2)
        activity_type = str(profile.get("activity_type") or "")
        if activity_type in {"Serviços", "Misto"} or not activity_type:
            if q1.button("Importar NFS-e", width="stretch"):
                navigate("Importar NFS-e")
        else:
            if q1.button("Abrir notas fiscais", width="stretch"):
                navigate("Notas Fiscais")
        if q2.button("Abrir documentos", width="stretch"):
            navigate("Documentos")

    with st.expander("Mais recursos fiscais"):
        st.caption("Recursos de revisão que não precisam ficar sempre visíveis.")
        b1, b2 = st.columns(2)
        if b1.button("Fechamento mensal", width="stretch"):
            navigate("Fechamento Mensal")
        if b2.button("Espaço do contador", width="stretch"):
            navigate("Espaço do Contador")
