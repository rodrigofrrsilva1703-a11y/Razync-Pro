from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from automation_tools import financial_projection, upcoming_deadlines
from customer_experience import build_today_plan
from fiscal_rules import das_status
from growth_tools import build_notifications
from onboarding_tools import onboarding_progress
from product_core import action_items
from smart_insights import build_proactive_insights
from ui_system import alert_card, section


def _health_score(profile: dict, annual_revenue: float, annual_limit: float, das_rows: list[dict], obligations: list[dict]) -> tuple[int, list[str]]:
    score = 100
    notes: list[str] = []
    if not profile.get("cnpj"):
        score -= 20
        notes.append("Complete o CNPJ do MEI.")
    if not profile.get("main_activity"):
        score -= 10
        notes.append("Informe a atividade principal.")
    if annual_limit and annual_revenue / annual_limit >= 0.90:
        score -= 20
        notes.append("O faturamento está próximo do limite monitorado.")
    overdue_das = sum(1 for row in das_rows if das_status(row.get("status", "Pendente"), row.get("due_date")) == "Atrasado")
    if overdue_das:
        score -= min(30, overdue_das * 10)
        notes.append(f"Existem {overdue_das} DAS em atraso.")
    overdue_obligations = 0
    today = date.today()
    for row in obligations:
        due = row.get("due_date")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due)
            except ValueError:
                due = None
        if row.get("status") != "Concluído" and due and due < today:
            overdue_obligations += 1
    if overdue_obligations:
        score -= min(20, overdue_obligations * 5)
        notes.append(f"Existem {overdue_obligations} obrigação(ões) vencida(s).")
    return max(score, 0), notes


def render_dashboard_workspace(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    annual_limit: float,
    annual_revenue: float,
    current_year: int,
    brl,
    navigate,
) -> None:
    today = date.today()
    month_tx = transactions[
        (transactions["tx_date"].dt.year == current_year)
        & (transactions["tx_date"].dt.month == today.month)
    ] if not transactions.empty else transactions
    month_in = float(month_tx[month_tx["tx_type"] == "Receita"]["value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx[month_tx["tx_type"] == "Despesa"]["value"].sum()) if not month_tx.empty else 0.0
    month_result = month_in - month_out

    st.markdown("### Hoje no seu MEI")
    st.caption("Uma visão curta do que entrou, do que saiu e do que precisa de atenção.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Entradas no mês", brl(month_in))
    k2.metric("Saídas no mês", brl(month_out))
    k3.metric("Resultado do mês", brl(month_result))
    k4.metric("Faturamento no ano", brl(annual_revenue))

    projection = financial_projection(transactions, annual_limit, current_year, today)
    if projection.get("limit_risk"):
        alert_card("warn", "Atenção ao limite do MEI", f"No ritmo atual, a projeção anual é {brl(projection['projected_revenue'])}.")

    priorities = action_items(profile, transactions, invoices, das_rows, obligations, annual_limit, annual_revenue)
    setup = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(documents))
    notifications = build_notifications(das_rows, obligations, annual_revenue, annual_limit)
    plan = build_today_plan(priorities, notifications, setup, limit=4)

    main_col, side_col = st.columns([1.65, 1], gap="large")
    with main_col:
        section("O que fazer agora", "As tarefas mais importantes, em ordem de prioridade.")
        if not plan["items"]:
            st.success("Nenhuma ação urgente identificada.")
        for idx, item in enumerate(plan["items"][:4]):
            row, action = st.columns([4.5, 1.2])
            with row:
                level = "danger" if item["priority"] == 1 else "warn" if item["priority"] == 2 else "info" if item["priority"] == 3 else "ok"
                alert_card(level, item["title"], item["detail"])
            with action:
                if item["page"] != "Dashboard" and st.button("Resolver", key=f"dashv2_action_{idx}", width="stretch"):
                    navigate(item["page"])

    with side_col:
        section("Saúde do MEI", "Limite, obrigações e organização em um único indicador.")
        score, notes = _health_score(profile, annual_revenue, annual_limit, das_rows, obligations)
        st.metric("Índice de organização", f"{score}/100")
        st.progress(score / 100)
        limit_pct = (annual_revenue / annual_limit * 100) if annual_limit else 0.0
        st.caption(f"Limite usado: {limit_pct:.1f}%")
        st.progress(min(max(limit_pct / 100, 0), 1.0))
        if notes:
            for note in notes[:3]:
                st.caption(f"• {note}")
        elif score >= 90:
            st.success("Seu MEI está bem organizado com os dados cadastrados.")

    insights = build_proactive_insights(
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        annual_limit=annual_limit,
        current_year=current_year,
        today=today,
    )
    section("Insights do Razync", "Sinais automáticos calculados com os dados já carregados. Nenhuma chamada de IA é feita nesta tela.")
    if not insights:
        st.info("Adicione mais movimentações e informações fiscais para o Razync identificar tendências automaticamente.")
    else:
        for idx, insight in enumerate(insights[:3]):
            info_col, open_col, ai_col = st.columns([4.8, 1, 1.35])
            with info_col:
                alert_card(insight["level"], insight["title"], insight["detail"])
            with open_col:
                if st.button("Abrir", key=f"smart_insight_open_{idx}", width="stretch"):
                    navigate(insight["page"])
            with ai_col:
                if st.button("Perguntar à IA", key=f"smart_insight_ai_{idx}", width="stretch"):
                    st.session_state["razync_ai_pending_question"] = insight["question"]
                    navigate("Assistente Razync")

    section("Acesso rápido", "Entre direto nas duas áreas principais ou registre uma movimentação.")
    q1, q2, q3 = st.columns(3)
    if q1.button("Financeiro", key="dashv2_finance", width="stretch"):
        navigate("Financeiro")
    if q2.button("Fiscal MEI", key="dashv2_fiscal", width="stretch"):
        navigate("Fiscal")
    if q3.button("Nova movimentação", key="dashv2_new_tx", width="stretch"):
        navigate("Movimentações")

    deadlines = upcoming_deadlines(das_rows, obligations, today=today, days=30)
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        section("Próximos vencimentos", "Somente o que pode exigir ação nos próximos 30 dias.")
        if deadlines:
            for idx, item in enumerate(deadlines[:4]):
                due, title, action = st.columns([1, 3.4, 1])
                due.caption(item["date"].strftime("%d/%m"))
                title.write(f"**{item['title']}**")
                title.caption(item["status"])
                if action.button("Abrir", key=f"dashv2_deadline_{idx}", width="stretch"):
                    navigate(item["page"])
        else:
            st.success("Nenhum vencimento cadastrado para os próximos 30 dias.")

    with right:
        section("Últimos lançamentos", "Os registros financeiros mais recentes.")
        if transactions.empty:
            st.info("Ainda não há movimentações cadastradas.")
        else:
            recent = transactions.sort_values("tx_date", ascending=False).head(5).copy()
            recent["Data"] = pd.to_datetime(recent["tx_date"]).dt.strftime("%d/%m")
            recent["Valor"] = recent["value"].map(brl)
            recent["Descrição"] = recent["description"].fillna("Sem descrição")
            recent["Tipo"] = recent["tx_type"]
            st.dataframe(recent[["Data", "Tipo", "Descrição", "Valor"]], hide_index=True, width="stretch")

    if setup["percent"] < 100:
        with st.expander(f"Configuração do MEI · {setup['percent']}% concluída"):
            st.progress(setup["percent"] / 100)
            st.caption("Complete o cadastro inicial para melhorar alertas, relatórios e automações.")
            if st.button("Continuar configuração", key="dashv2_onboarding", width="stretch"):
                navigate("Primeiros Passos")
