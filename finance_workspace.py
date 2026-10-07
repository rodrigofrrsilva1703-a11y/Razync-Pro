from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from automation_tools import financial_projection
from business_tools import financial_analysis
from compact_cards import stat_card
from product_core import reconciliation_summary
from table_ui import professional_table
from ui_system import alert_card, apply_plot_theme, empty_state


def render_finance_workspace(
    *,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    annual_limit: float,
    current_year: int,
    opening_date,
    theme: str,
    brl,
    navigate,
) -> None:
    """Editorial finance workspace with a single primary flow."""
    today = date.today()
    year_tx = (
        transactions[transactions["tx_date"].dt.year == current_year]
        if not transactions.empty else transactions
    )
    month_tx = (
        year_tx[year_tx["tx_date"].dt.month == today.month]
        if not year_tx.empty else year_tx
    )

    month_in = float(month_tx.loc[month_tx["tx_type"] == "Receita", "value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx.loc[month_tx["tx_type"] == "Despesa", "value"].sum()) if not month_tx.empty else 0.0
    year_in = float(year_tx.loc[year_tx["tx_type"] == "Receita", "value"].sum()) if not year_tx.empty else 0.0
    year_out = float(year_tx.loc[year_tx["tx_type"] == "Despesa", "value"].sum()) if not year_tx.empty else 0.0
    month_result = month_in - month_out
    year_result = year_in - year_out

    with st.container(key="workspace_metrics"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            stat_card("Entradas", brl(month_in), detail="Sem lançamentos no mês" if month_tx.empty else "mês atual")
        with c2:
            stat_card("Saídas", brl(month_out), detail="Sem lançamentos no mês" if month_tx.empty else "mês atual")
        with c3:
            stat_card(
                "Resultado",
                brl(month_result),
                detail="Sem lançamentos no mês" if month_tx.empty else "mês atual",
                tone="neutral" if month_tx.empty else "positive" if month_result >= 0 else "danger",
            )
        with c4:
            stat_card(
                "Resultado anual",
                brl(year_result),
                detail=f"{current_year}",
                tone="neutral" if year_tx.empty else "positive" if year_result >= 0 else "danger",
            )

    projection = financial_projection(
        transactions,
        annual_limit,
        current_year,
        today,
        opening_date=opening_date,
    )
    if projection.get("limit_risk"):
        alert_card(
            "warn",
            "Ritmo de faturamento acima do ideal",
            f"A projeção anual atual é {brl(projection['projected_revenue'])}.",
        )

    a1, a2, spacer = st.columns([1, 1, 2.8], gap="small")
    if a1.button("＋ Nova movimentação", type="primary", width="stretch"):
        navigate("Movimentações")
    if a2.button("Importar extrato", width="stretch"):
        navigate("Importar Extrato")

    st.markdown("#### Evolução")
    chart_col, review_col = st.columns([1.7, 1], gap="large")

    with chart_col, st.container(key="overview_panel_finance_chart"):
        if year_tx.empty:
            empty_state(
                "Seu financeiro começa aqui",
                "Registre a primeira entrada ou despesa, ou importe seu extrato nos botões acima. A evolução do ano aparecerá neste espaço.",
                "↗",
            )
        else:
            import plotly.express as px

            monthly = year_tx.assign(Mês=year_tx["tx_date"].dt.to_period("M").astype(str))
            grouped = monthly.pivot_table(
                index="Mês",
                columns="tx_type",
                values="value",
                aggfunc="sum",
                fill_value=0,
            ).reset_index()
            for column in ("Receita", "Despesa"):
                if column not in grouped:
                    grouped[column] = 0.0
            grouped["Resultado"] = grouped["Receita"] - grouped["Despesa"]
            month_names = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
            grouped["Período"] = [
                f"{month_names[int(value[5:7]) - 1]}/{value[:4]}"
                for value in grouped["Mês"]
            ]
            fig = px.line(
                grouped,
                x="Período",
                y=["Receita", "Despesa", "Resultado"],
                markers=True,
                color_discrete_map={
                    "Receita": "#168f80",
                    "Despesa": "#b8756b",
                    "Resultado": "#6b97a8",
                },
            )
            apply_plot_theme(fig, theme, height=310)
            fig.update_layout(
                xaxis_title=None,
                yaxis_title=None,
                legend_title_text=None,
                margin=dict(l=0, r=0, t=8, b=0),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with review_col, st.container(key="overview_panel_finance_review"):
        st.caption("REVISÃO")
        rec = reconciliation_summary(transactions, invoices)
        st.markdown(
            f"""
            <div class="rz-health-row"><span>Notas sem conciliação</span><strong>{len(rec['pending_invoices'])}</strong></div>
            <div class="rz-health-row"><span>Possíveis duplicidades</span><strong>{rec['possible_duplicate_transactions']}</strong></div>
            <div class="rz-health-row"><span>Receitas no ano</span><strong>{brl(year_in)}</strong></div>
            <div class="rz-health-row"><span>Despesas no ano</span><strong>{brl(year_out)}</strong></div>
            """,
            unsafe_allow_html=True,
        )
        if len(rec["pending_invoices"]) or rec["possible_duplicate_transactions"]:
            if st.button("Abrir conciliação", key="finance_review_reconciliation"):
                navigate("Conciliação")
        elif transactions.empty and invoices.empty:
            st.caption("A conciliação será exibida após cadastrar movimentações e notas.")
        else:
            st.caption("Nenhuma pendência evidente.")

    st.markdown("#### Movimentações recentes")
    if transactions.empty:
        st.caption("Nenhuma movimentação registrada.")
    else:
        recent = transactions.sort_values("tx_date", ascending=False).head(8).copy()
        professional_table(
            recent[["tx_date", "tx_type", "description", "value"]],
            max_visible_rows=8,
            column_config={
                "tx_date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "tx_type": "Tipo",
                "description": "Descrição",
                "value": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            },
        )

    with st.expander("Planejamento e ferramentas"):
        analysis = financial_analysis(transactions, current_year)
        p1, p2, p3 = st.columns(3)
        with p1:
            stat_card("Receita anual", brl(analysis["revenue"]))
        with p2:
            stat_card("Despesa anual", brl(analysis["expense"]))
        with p3:
            stat_card("Margem", f"{analysis['margin']:.1f}%")

        b1, b2, b3 = st.columns(3)
        if b1.button("Conciliação", width="stretch"):
            navigate("Conciliação")
        if b2.button("Fluxo de caixa", width="stretch"):
            navigate("Fluxo de Caixa")
        if b3.button("Análise completa", width="stretch"):
            navigate("Análise Financeira")
