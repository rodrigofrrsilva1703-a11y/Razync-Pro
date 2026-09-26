from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from activity_center import build_activity_items, render_activity_center
from automation_tools import upcoming_deadlines
from customer_experience import build_today_plan
from growth_tools import build_notifications
from onboarding_tools import onboarding_progress
from product_core import action_items
from smart_insights import build_proactive_insights
from table_ui import professional_table


def render_dashboard_workspace(
    *, profile: dict, transactions: pd.DataFrame, invoices: pd.DataFrame,
    das_rows: list[dict], obligations: list[dict], documents: list[dict],
    annual_limit: float, annual_revenue: float, current_year: int, brl, navigate,
) -> None:
    today = date.today()
    month_tx = transactions[
        (transactions["tx_date"].dt.year == current_year)
        & (transactions["tx_date"].dt.month == today.month)
    ] if not transactions.empty else transactions
    month_in = float(month_tx.loc[month_tx["tx_type"] == "Receita", "value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx.loc[month_tx["tx_type"] == "Despesa", "value"].sum()) if not month_tx.empty else 0.0
    setup = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(documents))
    priorities = action_items(profile, transactions, invoices, das_rows, obligations, annual_limit, annual_revenue)
    notifications = build_notifications(das_rows, obligations, annual_revenue, annual_limit)
    tasks = build_today_plan(priorities, notifications, setup, limit=4)["items"]
    business = escape(str(profile.get("trade_name") or profile.get("business_name") or "seu MEI"))

    st.markdown(
        f'<div class="rz-dash-intro"><span>PAINEL DO MEI</span><h2>Vamos cuidar de {business}</h2>'
        '<p>Comece pela tarefa abaixo. O restante fica organizado para quando você precisar.</p></div>',
        unsafe_allow_html=True,
    )
    focus, summary = st.columns([1.55, 1], gap="large")
    with focus, st.container(key="dashboard_focus"):
        st.caption("PRÓXIMO PASSO")
        if tasks:
            task = tasks[0]
            st.markdown(f"### {task['title']}")
            st.write(task["detail"])
            if task["page"] != "Dashboard" and st.button("Resolver agora", key="dash_primary_next", type="primary", width="stretch"):
                navigate(task["page"])
        else:
            st.markdown("### Tudo em dia por enquanto")
            st.write("Quando houver algo para conferir, sua próxima tarefa aparecerá aqui.")
        if setup["percent"] < 100:
            st.caption(f"Cadastro inicial: {setup['percent']}% concluído")

    with summary, st.container(key="dashboard_summary"):
        st.caption("SEU DINHEIRO NESTE MÊS")
        st.metric("Entradas menos saídas", brl(month_in - month_out))
        left, right = st.columns(2)
        left.metric("Entrou", brl(month_in))
        right.metric("Saiu", brl(month_out))
        if st.button("Ver meu financeiro", key="dash_open_finance", width="stretch"):
            navigate("Financeiro")

    st.markdown("#### O que você quer fazer?")
    action_a, action_b, action_c = st.columns(3, gap="medium")
    with action_a, st.container(key="dashboard_action_register"):
        if st.button("＋  Registrar entrada ou saída", key="rz_quick_card_new_tx", width="stretch"):
            navigate("Movimentações")
    with action_b, st.container(key="dashboard_action_import"):
        if st.button("↥  Importar extrato do banco", key="rz_quick_card_import", width="stretch"):
            navigate("Importar Extrato")
    with action_c, st.container(key="dashboard_action_help"):
        if st.button("✦  Pedir ajuda ao Razync", key="rz_quick_card_ai", width="stretch"):
            st.session_state["razync_floating_open"] = True
            st.rerun()

    task_col, deadline_col = st.columns(2, gap="large")
    with task_col:
        st.markdown("#### Depois disso")
        if len(tasks) <= 1:
            st.caption("Suas próximas tarefas aparecerão aqui.")
        for index, task in enumerate(tasks[1:4], start=1):
            with st.container(key=f"dashboard_task_{index}"):
                st.markdown(f"**{task['title']}**")
                st.caption(task["detail"])
                if task["page"] != "Dashboard" and st.button("Abrir tarefa", key=f"dashboard_task_open_{index}", width="stretch"):
                    navigate(task["page"])

    with deadline_col:
        st.markdown("#### Próximos vencimentos")
        deadlines = upcoming_deadlines(das_rows, obligations, today=today, days=30)
        if not deadlines:
            st.caption("Nenhum vencimento cadastrado para os próximos 30 dias.")
        for index, deadline in enumerate(deadlines[:3]):
            with st.container(key=f"dashboard_deadline_{index}"):
                st.markdown(f"**{deadline['title']}** · {deadline['date'].strftime('%d/%m')}")
                st.caption(deadline["status"])
                if st.button("Ver prazo", key=f"dashboard_deadline_open_{index}", width="stretch"):
                    navigate(deadline["page"])

    with st.expander("Ver mais informações do meu MEI"):
        st.metric("Faturamento no ano", brl(annual_revenue))
        if annual_limit:
            st.progress(min(max(annual_revenue / annual_limit, 0), 1))
            st.caption(f"{annual_revenue / annual_limit:.1%} do limite anual monitorado")
        if setup["percent"] < 100 and st.button("Continuar meu cadastro", key="dash_onboarding"):
            navigate("Primeiros Passos")
        st.markdown("##### Últimos lançamentos")
        if transactions.empty:
            st.caption("Nenhuma entrada ou saída cadastrada ainda.")
        else:
            recent = transactions.sort_values("tx_date", ascending=False).head(5).copy()
            recent["Data"] = pd.to_datetime(recent["tx_date"]).dt.strftime("%d/%m")
            recent["Valor"] = recent["value"].map(brl)
            recent["Descrição"] = recent["description"].fillna("Sem descrição")
            recent["Tipo"] = recent["tx_type"]
            professional_table(recent[["Data", "Tipo", "Descrição", "Valor"]], max_visible_rows=5)
            if st.button("Ver todas as entradas e saídas", key="dash_recent_all"):
                navigate("Movimentações")
        activity_items = build_activity_items(
            profile=profile, transactions=transactions, das_rows=das_rows,
            obligations=obligations, documents=documents, today=today,
        )
        render_activity_center(items=activity_items, navigate=navigate)
        insights = build_proactive_insights(
            profile=profile, transactions=transactions, invoices=invoices,
            das_rows=das_rows, obligations=obligations, documents=documents,
            annual_limit=annual_limit, current_year=current_year, today=today,
        )
        for index, insight in enumerate(insights[:2]):
            st.markdown(f"**{insight['title']}**")
            st.caption(insight["detail"])
            if st.button("Ver análise", key=f"dash_insight_{index}"):
                navigate(insight["page"])
            if st.button("Pedir explicação à IA", key=f"dash_insight_ai_{index}"):
                st.session_state["razync_ai_pending_question"] = insight["question"]
                st.session_state["razync_ai_pending_context"] = {
                    "source": "dashboard_insight", "title": insight["title"],
                    "detail": insight["detail"], "page": insight["page"],
                }
                st.session_state["razync_floating_open"] = True
                st.rerun()
