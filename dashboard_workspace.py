from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from automation_tools import upcoming_deadlines
from compact_cards import stat_card
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
    """Editorial home: numbers first, one focal action, quiet lists."""
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

    business_name = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"
    cnpj = str(profile.get("cnpj") or "").strip()
    business_meta = f"MEI · {current_year}"
    if cnpj:
        business_meta += f" · {cnpj}"
    st.markdown(
        f'<div class="rz-dash-intro"><span>{business_name}</span>'
        f'<p>{business_meta}</p></div>',
        unsafe_allow_html=True,
    )

    # One quiet financial strip.
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        stat_card("Entradas", brl(month_in), detail="este mês")
    with m2:
        stat_card("Saídas", brl(month_out), detail="este mês")
    with m3:
        stat_card(
            "Resultado",
            brl(month_result),
            detail="este mês",
            tone="positive" if month_result >= 0 else "danger",
        )
    with m4:
        stat_card(
            "Limite MEI",
            f"{limit_pct:.1f}%",
            detail=f"{brl(annual_revenue)} no ano",
            tone="warning" if limit_pct >= 80 else "neutral",
        )

    st.markdown("<div style='height:1.05rem'></div>", unsafe_allow_html=True)

    # One focal block + one plain status rail.
    focus, status = st.columns([1.65, 1], gap="large")
    with focus, st.container(key="dashboard_focus"):
        st.caption("O QUE MERECE ATENÇÃO AGORA")
        if tasks:
            task = tasks[0]
            st.markdown(f"### {task['title']}")
            st.write(task["detail"])
            if task["page"] != "Dashboard" and st.button(
                "Abrir",
                key="dash_primary_next",
                type="primary",
            ):
                navigate(task["page"])
        else:
            st.markdown("### Nada urgente por enquanto")
            st.write("Seu workspace não tem nenhuma ação prioritária neste momento.")

    with status, st.container(key="dashboard_health"):
        open_tasks = len([item for item in tasks if item.get("page") != "Dashboard"])
        st.markdown(
            f"""
            <div class="rz-health-head">
              <strong>Estado do workspace</strong>
              <span class="rz-health-pill">{current_year}</span>
            </div>
            <div class="rz-health-row"><span>Configuração</span><strong>{setup['percent']}%</strong></div>
            <div class="rz-health-row"><span>Faturamento anual</span><strong>{brl(annual_revenue)}</strong></div>
            <div class="rz-health-row"><span>Vencimentos em 30 dias</span><strong>{len(deadlines)}</strong></div>
            <div class="rz-health-row"><span>Pontos de atenção</span><strong>{open_tasks}</strong></div>
            """,
            unsafe_allow_html=True,
        )

    # Tiny utility row, not a command dashboard.
    action_a, action_b, spacer = st.columns([1, 1, 2.8], gap="small")
    if action_a.button("＋ Movimentação", key="dashboard_new_tx", type="primary", width="stretch"):
        navigate("Movimentações")
    if action_b.button("Importar extrato", key="dashboard_import_statement", width="stretch"):
        navigate("Importar Extrato")

    st.markdown("#### Hoje")
    task_col, deadline_col = st.columns(2, gap="large")
    with task_col:
        st.caption("PRÓXIMAS TAREFAS")
        next_tasks = tasks[1:4] if len(tasks) > 1 else []
        if not next_tasks:
            st.write("Nenhuma outra tarefa importante.")
        for index, task in enumerate(next_tasks, start=1):
            with st.container(key=f"dashboard_task_{index}"):
                st.markdown(f"**{task['title']}**")
                st.caption(task["detail"])

    with deadline_col:
        st.caption("PRÓXIMOS VENCIMENTOS")
        if not deadlines:
            st.write("Nenhum vencimento identificado nos próximos 30 dias.")
        for index, deadline in enumerate(deadlines[:3]):
            with st.container(key=f"dashboard_deadline_{index}"):
                st.markdown(
                    f"**{deadline['date'].strftime('%d/%m')}** · {deadline['title']}"
                )
                st.caption(deadline["status"])
        if deadlines and st.button(
            "Ver agenda completa",
            key="dashboard_open_obligations",
        ):
            navigate("Obrigações")

    st.markdown("#### Movimento recente")
    if transactions.empty:
        st.caption("Nenhuma movimentação registrada.")
    else:
        recent = transactions.sort_values("tx_date", ascending=False).head(6).copy()
        recent["Data"] = pd.to_datetime(recent["tx_date"]).dt.date
        recent["Descrição"] = recent["description"].fillna("Sem descrição")
        recent["Tipo"] = recent["tx_type"]
        recent["Valor"] = recent["value"]
        professional_table(
            recent[["Data", "Tipo", "Descrição", "Valor"]],
            max_visible_rows=6,
            column_config={
                "Data": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )

    with st.expander("Mais contexto"):
        st.markdown("##### Limite anual")
        st.progress(min(max(annual_revenue / annual_limit, 0), 1) if annual_limit else 0)
        st.caption(
            f"{limit_pct:.1f}% do limite anual monitorado"
            if annual_limit else "Limite anual ainda não definido."
        )

        if insights:
            st.markdown("##### Insights")
            for index, insight in enumerate(insights[:2]):
                st.markdown(f"**{insight['title']}**")
                st.caption(insight["detail"])
                if st.button(
                    "Abrir análise",
                    key=f"dash_insight_{index}",
                ):
                    navigate(insight["page"])
