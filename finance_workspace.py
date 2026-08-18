from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from automation_tools import financial_projection
from business_tools import financial_analysis
from product_core import reconciliation_summary
from ui_system import alert_card, apply_plot_theme, section, tokens


def render_finance_workspace(
    *,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    annual_limit: float,
    current_year: int,
    theme: str,
    brl,
    navigate,
) -> None:
    """Integrated daily financial workspace for the MEI."""
    today = date.today()
    year_tx = transactions[transactions["tx_date"].dt.year == current_year] if not transactions.empty else transactions
    month_tx = year_tx[year_tx["tx_date"].dt.month == today.month] if not year_tx.empty else year_tx
    month_in = float(month_tx[month_tx["tx_type"] == "Receita"]["value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx[month_tx["tx_type"] == "Despesa"]["value"].sum()) if not month_tx.empty else 0.0
    year_in = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
    year_out = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0

    st.markdown("### Financeiro")
    st.caption("Registre, confira e entenda o dinheiro do MEI em uma única área.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entradas no mês", brl(month_in))
    c2.metric("Saídas no mês", brl(month_out))
    c3.metric("Resultado no mês", brl(month_in - month_out))
    c4.metric("Resultado no ano", brl(year_in - year_out))

    projection = financial_projection(transactions, annual_limit, current_year, today)
    if projection.get("limit_risk"):
        alert_card("warn", "Atenção ao ritmo de faturamento", f"Projeção anual de {brl(projection['projected_revenue'])}.")

    section("Ações do dia", "As rotinas financeiras mais usadas ficam juntas aqui.")
    a1, a2, a3, a4 = st.columns(4)
    if a1.button("Nova movimentação", width="stretch"):
        navigate("Movimentações")
    if a2.button("Importar extrato", width="stretch"):
        navigate("Importar Extrato")
    if a3.button("Conciliar", width="stretch"):
        navigate("Conciliação")
    if a4.button("Recorrências", width="stretch"):
        navigate("Recorrências")

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        section("Evolução mensal", "Entradas, saídas e resultado do ano atual.")
        if year_tx.empty:
            st.info("Registre uma movimentação para começar a acompanhar a evolução financeira.")
        else:
            monthly = year_tx.assign(Mês=year_tx["tx_date"].dt.to_period("M").astype(str))
            grouped = monthly.pivot_table(index="Mês", columns="tx_type", values="value", aggfunc="sum", fill_value=0).reset_index()
            for col in ["Receita", "Despesa"]:
                if col not in grouped:
                    grouped[col] = 0.0
            grouped["Resultado"] = grouped["Receita"] - grouped["Despesa"]
            fig = px.line(grouped, x="Mês", y=["Receita", "Despesa", "Resultado"], markers=True)
            apply_plot_theme(fig, theme, height=330)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with right:
        section("Conciliação", "Notas e lançamentos que ainda merecem revisão.")
        rec = reconciliation_summary(transactions, invoices)
        st.metric("Notas pendentes", len(rec["pending_invoices"]))
        st.metric("Possíveis duplicidades", rec["possible_duplicate_transactions"])
        if len(rec["pending_invoices"]) or rec["possible_duplicate_transactions"]:
            if st.button("Abrir conciliação financeira", width="stretch"):
                navigate("Conciliação")
        else:
            st.success("Nenhuma pendência evidente encontrada.")

    section("Leitura financeira", "Uma visão resumida para decidir sem abrir várias telas.")
    analysis = financial_analysis(transactions, current_year)
    x1, x2, x3 = st.columns(3)
    x1.metric("Receitas no ano", brl(analysis["revenue"]))
    x2.metric("Despesas no ano", brl(analysis["expense"]))
    x3.metric("Margem", f"{analysis['margin']:.1f}%")

    if not transactions.empty:
        recent = transactions.sort_values("tx_date", ascending=False).head(6).copy()
        st.dataframe(
            recent[["tx_date", "tx_type", "description", "value"]],
            width="stretch",
            hide_index=True,
            column_config={
                "tx_date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "tx_type": "Tipo",
                "description": "Descrição",
                "value": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
            },
        )

    with st.expander("Ferramentas financeiras avançadas"):
        b1, b2 = st.columns(2)
        if b1.button("Fluxo de caixa", width="stretch"):
            navigate("Fluxo de Caixa")
        if b2.button("Análise financeira completa", width="stretch"):
            navigate("Análise Financeira")
