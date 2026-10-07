from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from business_tools import monthly_closing
from compact_cards import stat_card
from fiscal_rules import das_status
from mei_obligations import upcoming_automatic_obligations
from fiscal_timeline import build_fiscal_timeline, render_fiscal_timeline
from table_ui import professional_table
from ui_system import alert_card


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
    """Editorial fiscal workspace focused on status and deadlines."""
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
        stat_card(
            "DAS em atraso",
            str(len(overdue_das)),
            detail="competências",
            tone="danger" if overdue_das else "neutral",
        )
    with c2:
        stat_card(
            "DAS pendentes",
            str(len(pending_das)),
            detail="competências",
            tone="warning" if pending_das else "neutral",
        )
    with c3:
        stat_card("Notas", str(len(invoices)), detail="cadastradas")
    with c4:
        stat_card(
            "Limite MEI",
            f"{limit_pct:.1f}%",
            detail=f"{brl(annual_revenue)} no ano",
            tone="warning" if limit_pct >= 80 else "neutral",
        )

    if overdue_das:
        alert_card(
            "danger",
            "Existe DAS em atraso",
            f"{len(overdue_das)} competência(s) precisam de revisão.",
        )
    elif overdue_obligations:
        alert_card(
            "warn",
            "Há obrigação vencida",
            f"{len(overdue_obligations)} item(ns) precisam de revisão.",
        )

    a1, a2, spacer = st.columns([1, 1, 2.8], gap="small")
    if a1.button("DAS mensal", type="primary", width="stretch"):
        navigate("DAS")
    if a2.button("Notas fiscais", width="stretch"):
        navigate("Notas Fiscais")

    st.markdown("#### Situação fiscal")
    das_col, closing_col = st.columns([1.65, 1], gap="large")

    with das_col:
        st.caption("COMPETÊNCIAS CONTROLADAS")
        if not das_rows:
            st.caption("Nenhuma competência do DAS foi cadastrada.")
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

    with closing_col:
        st.caption("FECHAMENTO DO MÊS")
        closing = monthly_closing(
            transactions,
            invoices,
            documents,
            das_rows,
            today.year,
            today.month,
        )
        st.markdown(
            f"""
            <div class="rz-health-row"><span>Organização</span><strong>{closing['score']}%</strong></div>
            <div class="rz-health-row"><span>Notas cadastradas</span><strong>{len(invoices)}</strong></div>
            <div class="rz-health-row"><span>Documentos</span><strong>{len(documents)}</strong></div>
            <div class="rz-health-row"><span>Obrigações vencidas</span><strong>{len(overdue_obligations)}</strong></div>
            """,
            unsafe_allow_html=True,
        )
        pending = [item for item in closing["checklist"] if not item["OK"]]
        if pending:
            st.caption("Pontos a revisar:")
            for item in pending[:3]:
                st.caption(f"• {item['Item']}")
            if st.button("Abrir fechamento", key="fiscal_open_closing"):
                navigate("Fechamento Mensal")
        else:
            st.caption("Nenhum ponto básico pendente no checklist.")

    st.markdown("#### Próximos prazos")
    timeline_items = build_fiscal_timeline(
        das_rows=das_rows,
        obligations=[*obligations, *automatic_upcoming],
        today=today,
        days_ahead=90,
    )
    if timeline_items:
        render_fiscal_timeline(items=timeline_items, navigate=navigate)
    else:
        st.caption("Nenhum prazo identificado nos próximos 90 dias.")

    with st.expander("Relatórios e ferramentas"):
        r1, r2, r3 = st.columns(3)
        with r1:
            stat_card("Faturamento anual", brl(annual_revenue))
        with r2:
            stat_card("Documentos", str(len(documents)))
        with r3:
            stat_card("Notas fiscais", str(len(invoices)))

        b1, b2, b3 = st.columns(3)
        if b1.button("Obrigações", width="stretch"):
            navigate("Obrigações")
        if b2.button("Relatório mensal", width="stretch"):
            navigate("Relatório Mensal")
        if b3.button("Declaração anual", width="stretch"):
            navigate("DASN-SIMEI")

        c1, c2 = st.columns(2)
        if c1.button("Documentos", width="stretch"):
            navigate("Documentos")
        if c2.button("Espaço do contador", width="stretch"):
            navigate("Espaço do Contador")
