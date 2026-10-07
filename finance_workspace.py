from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from automation_tools import financial_projection
from business_tools import financial_analysis
from compact_cards import stat_card
from contextual_ai import contextual_ai_button
from product_core import reconciliation_summary
from table_ui import professional_table
from ui_system import alert_card, apply_plot_theme, section


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
    """Daily financial workspace focused on fast decisions."""
    today = date.today()
    year_tx = transactions[transactions["tx_date"].dt.year == current_year] if not transactions.empty else transactions
    month_tx = year_tx[year_tx["tx_date"].dt.month == today.month] if not year_tx.empty else year_tx
    month_in = float(month_tx[month_tx["tx_type"] == "Receita"]["value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx[month_tx["tx_type"] == "Despesa"]["value"].sum()) if not month_tx.empty else 0.0
    year_in = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
    year_out = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("Entradas no mês", brl(month_in))
    with c2:
        stat_card("Saídas no mês", brl(month_out))
    with c3:
        month_result = month_in - month_out
        stat_card("Resultado no mês", brl(month_result), tone="positive" if month_result >= 0 else "danger")
    with c4:
        year_result = year_in - year_out
        stat_card("Resultado no ano", brl(year_result), tone="positive" if year_result >= 0 else "danger")

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
            "Atenção ao ritmo de faturamento",
            f"Se o ritmo atual continuar, a projeção anual é {brl(projection['projected_revenue'])}.",
        )

    a1, a2, spacer = st.columns([1, 1, 2.1], gap="small")
    if a1.button("＋ Nova movimentação", type="primary", width="stretch"):
        navigate("Movimentações")
    if a2.button("Importar extrato", width="stretch"):
        navigate("Importar Extrato")

    with st.expander("Outras rotinas financeiras"):
        x1, x2, x3 = st.columns(3)
        if x1.button("Conciliação", width="stretch"):
            navigate("Conciliação")
        if x2.button("Recorrências", width="stretch"):
            navigate("Recorrências")
        if x3.button("Fluxo de caixa", width="stretch"):
            navigate("Fluxo de Caixa")

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        section("Evolução mensal", "Entradas, saídas e resultado do ano atual.")
        if year_tx.empty:
            st.info("Registre uma movimentação para começar a acompanhar a evolução financeira.")
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
            for col in ("Receita", "Despesa"):
                if col not in grouped:
                    grouped[col] = 0.0
            grouped["Resultado"] = grouped["Receita"] - grouped["Despesa"]
            month_names = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
            grouped["Período"] = [
                f"{month_names[int(month[5:7]) - 1]}/{month[:4]}" for month in grouped["Mês"]
            ]
            fig = px.line(
                grouped,
                x="Período",
                y=["Receita", "Despesa", "Resultado"],
                markers=True,
                color_discrete_map={
                    "Receita": "#10bdf2",
                    "Despesa": "#8fa9bc",
                    "Resultado": "#ef7479",
                },
            )
            apply_plot_theme(fig, theme, height=292)
            fig.update_layout(
                xaxis_title=None,
                yaxis_title=None,
                legend_title_text=None,
                font_color="#c7d8e6" if theme == "Escuro" else "#314657",
                legend_font_color="#c7d8e6" if theme == "Escuro" else "#314657",
                margin=dict(l=8, r=8, t=18, b=8),
            )
            fig.update_xaxes(type="category")
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with right:
        section("Conciliação", "O que ainda merece revisão.")
        rec = reconciliation_summary(transactions, invoices)
        r1, r2 = st.columns(2)
        with r1:
            stat_card("Notas pendentes", str(len(rec["pending_invoices"])))
        with r2:
            stat_card("Duplicidades possíveis", str(rec["possible_duplicate_transactions"]))
        if len(rec["pending_invoices"]) or rec["possible_duplicate_transactions"]:
            if st.button("Revisar conciliação", key="finance_review_reconciliation", width="stretch"):
                navigate("Conciliação")
        else:
            st.success("Nenhuma pendência evidente encontrada.")

    with st.expander("Analisar com Razync IA"):
        st.caption("Use a IA quando quiser interpretação dos números, sem mudar seus dados.")
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

    with st.expander("Resumo anual e últimos lançamentos"):
        analysis = financial_analysis(transactions, current_year)
        x1, x2, x3 = st.columns(3)
        with x1:
            stat_card("Receitas no ano", brl(analysis["revenue"]))
        with x2:
            stat_card("Despesas no ano", brl(analysis["expense"]))
        with x3:
            stat_card("Margem", f"{analysis['margin']:.1f}%")

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

    with st.expander("Análises avançadas"):
        st.caption("Abra apenas quando precisar investigar o financeiro com mais detalhe.")
        if st.button("Abrir análise financeira completa", key="finance_open_full_analysis", width="stretch"):
            navigate("Análise Financeira")
