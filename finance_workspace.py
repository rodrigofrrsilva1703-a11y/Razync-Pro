from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from automation_tools import financial_projection
from business_tools import financial_analysis
from compact_cards import metric_card
from contextual_ai import contextual_ai_button
from product_core import reconciliation_summary
from ui_system import alert_card, apply_plot_theme, section, tokens
from table_ui import professional_table


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
    with c1:
        if metric_card("Entradas no mês", brl(month_in), key="fin_month_in", help_text="Ver os lançamentos financeiros"):
            navigate("Movimentações")
    with c2:
        if metric_card("Saídas no mês", brl(month_out), key="fin_month_out", help_text="Ver os lançamentos financeiros"):
            navigate("Movimentações")
    with c3:
        if metric_card("Resultado no mês", brl(month_in - month_out), key="fin_month_result", help_text="Abrir a análise financeira"):
            navigate("Análise Financeira")
    with c4:
        if metric_card("Resultado no ano", brl(year_in - year_out), key="fin_year_result", help_text="Abrir a análise financeira completa"):
            navigate("Análise Financeira")

    ai1, ai2, ai3 = st.columns(3)
    with ai1:
        contextual_ai_button(
            "Analisar este mês",
            key="finance_month",
            navigate=navigate,
            source="finance_workspace",
            title="Análise financeira do mês",
            question="Analise minhas receitas, despesas e resultado deste mês. Destaque o que mais importa e sugira próximos passos.",
            detail=f"Entradas {brl(month_in)}; saídas {brl(month_out)}; resultado {brl(month_in - month_out)}.",
            page="Financeiro",
        )
    with ai2:
        contextual_ai_button(
            "Revisar despesas",
            key="finance_expenses",
            navigate=navigate,
            source="finance_workspace",
            title="Revisão de despesas",
            question="Quais despesas mais pesam no meu negócio e o que devo revisar primeiro? Use meus dados cadastrados.",
            detail=f"Saídas no mês {brl(month_out)}; despesas no ano {brl(year_out)}.",
            page="Financeiro",
        )
    with ai3:
        contextual_ai_button(
            "Projetar próximos passos",
            key="finance_next_steps",
            navigate=navigate,
            source="finance_workspace",
            title="Próximos passos financeiros",
            question="Com base no meu financeiro atual, quais são as três próximas ações mais importantes para melhorar controle e caixa?",
            detail=f"Resultado no mês {brl(month_in - month_out)}; resultado no ano {brl(year_in - year_out)}.",
            page="Financeiro",
        )

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
            apply_plot_theme(fig, theme, height=300)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with right:
        section("Conciliação", "Notas e lançamentos que ainda merecem revisão.")
        rec = reconciliation_summary(transactions, invoices)
        if metric_card("Notas pendentes", str(len(rec["pending_invoices"])), key="fin_pending_invoices", help_text="Abrir conciliação"):
            navigate("Conciliação")
        if metric_card("Possíveis duplicidades", str(rec["possible_duplicate_transactions"]), key="fin_duplicates", help_text="Abrir conciliação"):
            navigate("Conciliação")
        if not len(rec["pending_invoices"]) and not rec["possible_duplicate_transactions"]:
            st.success("Nenhuma pendência evidente encontrada.")

    with st.expander("Resumo anual e últimos lançamentos"):
        analysis = financial_analysis(transactions, current_year)
        x1, x2, x3 = st.columns(3)
        with x1:
            if metric_card("Receitas no ano", brl(analysis["revenue"]), key="fin_year_revenue", help_text="Abrir análise financeira"):
                navigate("Análise Financeira")
        with x2:
            if metric_card("Despesas no ano", brl(analysis["expense"]), key="fin_year_expense", help_text="Abrir análise financeira"):
                navigate("Análise Financeira")
        with x3:
            if metric_card("Margem", f"{analysis['margin']:.1f}%", key="fin_margin", help_text="Abrir análise financeira"):
                navigate("Análise Financeira")

        if not transactions.empty:
            recent = transactions.sort_values("tx_date", ascending=False).head(6).copy()
            professional_table(
                recent[["tx_date", "tx_type", "description", "value"]],
                max_visible_rows=6,
                column_config={
                    "tx_date": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "tx_type": "Tipo",
                    "description": "Descrição",
                    "value": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                },
            )
            if st.button("Ver todas as movimentações", key="finance_all_transactions", width="stretch"):
                navigate("Movimentações")

    with st.expander("Ferramentas financeiras avançadas"):
        b1, b2 = st.columns(2)
        if b1.button("Fluxo de caixa", width="stretch"):
            navigate("Fluxo de Caixa")
        if b2.button("Análise financeira completa", width="stretch"):
            navigate("Análise Financeira")
