from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from activity_center import build_activity_items, render_activity_center
from automation_tools import upcoming_deadlines
from compact_cards import metric_card
from customer_experience import build_today_plan
from growth_tools import build_notifications
from onboarding_tools import onboarding_progress
from mei_obligations import upcoming_automatic_obligations
from product_core import action_items
from smart_insights import build_proactive_insights
from table_ui import professional_table


def render_dashboard_workspace(
    *, profile: dict, transactions: pd.DataFrame, invoices: pd.DataFrame,
    das_rows: list[dict], obligations: list[dict], documents: list[dict],
    annual_limit: float, annual_revenue: float, current_year: int, brl, navigate,
) -> None:
    """Simple decision-first dashboard for the daily MEI routine."""
    today = date.today()
    month_tx = transactions[
        (transactions["tx_date"].dt.year == current_year)
        & (transactions["tx_date"].dt.month == today.month)
    ] if not transactions.empty else transactions
    month_in = float(month_tx.loc[month_tx["tx_type"] == "Receita", "value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx.loc[month_tx["tx_type"] == "Despesa", "value"].sum()) if not month_tx.empty else 0.0
    month_result = month_in - month_out
    limit_pct = (annual_revenue / annual_limit * 100) if annual_limit else 0.0

    setup = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(documents))
    priorities = action_items(
        profile, transactions, invoices, das_rows, obligations, annual_limit, annual_revenue
    )
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
        days_ahead=30,
    )
    reminder_obligations = [*obligations, *automatic_upcoming]
    notifications = build_notifications(
        das_rows,
        reminder_obligations,
        annual_revenue,
        annual_limit,
        today=today,
    )
    tasks = build_today_plan(priorities, notifications, setup, limit=4)["items"]
    deadlines = upcoming_deadlines(
        das_rows,
        reminder_obligations,
        today=today,
        days=30,
    )

    st.markdown(
        '<div class="rz-dash-intro"><div><span>SEU DIA EM ORDEM</span>'
        '<p>Veja os números essenciais e resolva primeiro o que precisa de atenção.</p></div></div>',
        unsafe_allow_html=True,
    )

    # The first scan of the page should answer: what came in, what went out,
    # what is left, and how much of the MEI limit is already used.
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        if metric_card("Entradas do mês", brl(month_in), key="dash_month_in", help_text="Abrir Financeiro"):
            navigate("Financeiro")
    with m2:
        if metric_card("Saídas do mês", brl(month_out), key="dash_month_out", help_text="Abrir Financeiro"):
            navigate("Financeiro")
    with m3:
        if metric_card("Resultado do mês", brl(month_result), key="dash_month_result", help_text="Abrir Financeiro"):
            navigate("Financeiro")
    with m4:
        if metric_card("Limite MEI usado", f"{limit_pct:.1f}%", key="dash_limit", help_text="Abrir Fiscal MEI"):
            navigate("Fiscal")

    focus, health = st.columns([1.55, 1], gap="large")
    with focus, st.container(key="dashboard_focus"):
        st.caption("PRÓXIMO PASSO")
        if tasks:
            task = tasks[0]
            st.markdown(f"### {task['title']}")
            st.write(task["detail"])
            if task["page"] != "Dashboard" and st.button(
                "Resolver agora",
                key="dash_primary_next",
                type="primary",
                width="stretch",
            ):
                navigate(task["page"])
        else:
            st.markdown("### Tudo em dia por enquanto")
            st.write("Quando houver algo importante para conferir, a próxima ação aparecerá aqui.")

    with health, st.container(key="dashboard_health"):
        open_tasks = len([task for task in tasks if task.get("page") != "Dashboard"])
        st.markdown(
            f"""
            <div class="rz-health-head">
              <strong>Visão rápida</strong>
              <span class="rz-health-pill">MEI {current_year}</span>
            </div>
            <div class="rz-health-row"><span>Cadastro inicial</span><strong>{setup['percent']}%</strong></div>
            <div class="rz-health-row"><span>Faturamento anual</span><strong>{brl(annual_revenue)}</strong></div>
            <div class="rz-health-row"><span>Próximos vencimentos</span><strong>{len(deadlines)}</strong></div>
            <div class="rz-health-row"><span>Ações prioritárias</span><strong>{open_tasks}</strong></div>
            """,
            unsafe_allow_html=True,
        )
        if setup["percent"] < 100:
            if st.button("Continuar configuração", key="dash_health_setup", width="stretch"):
                navigate("Primeiros Passos")
        else:
            if st.button("Ver dados do MEI", key="dash_health_mei", width="stretch"):
                navigate("Meu MEI")

    st.markdown("#### Ações rápidas")
    action_a, action_b, action_c = st.columns(3, gap="medium")
    with action_a, st.container(key="dashboard_action_register"):
        if st.button("＋  Registrar entrada ou saída", key="rz_quick_card_new_tx", width="stretch"):
            navigate("Movimentações")
    with action_b, st.container(key="dashboard_action_import"):
        if st.button("↥  Importar extrato bancário", key="rz_quick_card_import", width="stretch"):
            navigate("Importar Extrato")
    with action_c, st.container(key="dashboard_action_help"):
        if st.button("✦  Perguntar ao Razync", key="rz_quick_card_ai", width="stretch"):
            st.session_state["razync_floating_open"] = True
            st.rerun()

    task_col, deadline_col = st.columns(2, gap="large")
    with task_col:
        st.markdown("#### Próximas tarefas")
        next_tasks = tasks[1:4] if len(tasks) > 1 else []
        if not next_tasks:
            st.caption("Nenhuma outra tarefa importante para agora.")
        for index, task in enumerate(next_tasks, start=1):
            with st.container(key=f"dashboard_task_{index}"):
                st.markdown(f"**{task['title']}**")
                st.caption(task["detail"])
                if task["page"] != "Dashboard" and st.button(
                    "Abrir tarefa",
                    key=f"dashboard_task_open_{index}",
                    width="stretch",
                ):
                    navigate(task["page"])

    with deadline_col:
        st.markdown("#### Próximos vencimentos")
        if not deadlines:
            st.caption("Nenhum vencimento identificado para os próximos 30 dias.")
        for index, deadline in enumerate(deadlines[:3]):
            with st.container(key=f"dashboard_deadline_{index}"):
                st.markdown(f"**{deadline['title']}** · {deadline['date'].strftime('%d/%m')}")
                st.caption(deadline["status"])
                if st.button(
                    "Ver prazo",
                    key=f"dashboard_deadline_open_{index}",
                    width="stretch",
                ):
                    navigate(deadline["page"])

    with st.expander("Ver detalhes e histórico"):
        st.markdown("##### Faturamento anual")
        st.progress(min(max(annual_revenue / annual_limit, 0), 1) if annual_limit else 0)
        st.caption(
            f"{limit_pct:.1f}% do limite anual monitorado"
            if annual_limit else "Limite anual ainda não definido."
        )

        st.markdown("##### Últimos lançamentos")
        if transactions.empty:
            st.caption("Nenhuma entrada ou saída cadastrada ainda.")
        else:
            recent = transactions.sort_values("tx_date", ascending=False).head(5).copy()
            recent["Data"] = pd.to_datetime(recent["tx_date"]).dt.strftime("%d/%m")
            recent["Valor"] = recent["value"].map(brl)
            recent["Descrição"] = recent["description"].fillna("Sem descrição")
            recent["Tipo"] = recent["tx_type"]
            professional_table(
                recent[["Data", "Tipo", "Descrição", "Valor"]],
                max_visible_rows=5,
            )
            if st.button("Ver todas as entradas e saídas", key="dash_recent_all"):
                navigate("Movimentações")

        activity_items = build_activity_items(
            profile=profile,
            transactions=transactions,
            das_rows=das_rows,
            obligations=obligations,
            documents=documents,
            today=today,
        )
        render_activity_center(items=activity_items, navigate=navigate)

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
        if insights:
            st.markdown("##### Insights")
        for index, insight in enumerate(insights[:2]):
            st.markdown(f"**{insight['title']}**")
            st.caption(insight["detail"])
            c1, c2 = st.columns(2)
            if c1.button("Ver análise", key=f"dash_insight_{index}", width="stretch"):
                navigate(insight["page"])
            if c2.button("Explicar com IA", key=f"dash_insight_ai_{index}", width="stretch"):
                st.session_state["razync_ai_pending_question"] = insight["question"]
                st.session_state["razync_ai_pending_context"] = {
                    "source": "dashboard_insight",
                    "title": insight["title"],
                    "detail": insight["detail"],
                    "page": insight["page"],
                }
                st.session_state["razync_floating_open"] = True
                st.rerun()
