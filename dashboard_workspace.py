from __future__ import annotations

from datetime import date
from html import escape

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
    """Overview with one onboarding action, real financial data and a clear agenda."""
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
    month_names = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")
    month_label = f"{month_names[today.month - 1]} de {current_year}"
    st.markdown(
        f'<div class="rz-overview-head"><div><span class="rz-overline">{escape(str(business_name))} / Início</span>'
        '<h1>Visão geral</h1><p>Um olhar simples para o que importa no seu negócio.</p></div>'
        f'<div class="rz-period"><span aria-hidden="true">▦</span> {month_label}</div></div>',
        unsafe_allow_html=True,
    )

    with st.container(key="overview_welcome"):
        welcome, completion = st.columns([2.3, 1], gap="large")
        with welcome:
            st.caption("O QUE MERECE ATENÇÃO AGORA")
            task = tasks[0] if tasks else None
            title = "Seu MEI organizado começa aqui." if not setup["complete"] else "Mais controle. Mais tranquilidade."
            detail = task["detail"] if task else "Confira os números, acompanhe os prazos e siga com o seu dia."
            st.markdown(f'<div class="rz-welcome-title">{title}</div><p class="rz-welcome-copy">{escape(detail)}</p>', unsafe_allow_html=True)
            if task and task["page"] != "Dashboard" and st.button(task["title"] + "  →", key="dash_primary_next", type="primary"):
                navigate(task["page"])
        with completion:
            if not setup["complete"]:
                st.markdown(
                    f'<div class="rz-onboarding-summary"><span class="rz-overline">CONFIGURAÇÃO INICIAL</span>'
                    f'<p><strong>{setup["done"]}</strong> de {setup["total"]} etapas</p>'
                    f'<div class="rz-track" role="progressbar" aria-label="Configuração inicial" aria-valuenow="{setup["percent"]}" aria-valuemin="0" aria-valuemax="100"><i style="width:{setup["percent"]}%"></i></div>'
                    '<p>Avance no seu ritmo.</p></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="rz-onboarding-summary"><span class="rz-overline">SEU ESPAÇO ESTÁ PRONTO</span><p><strong>✓</strong></p><p>Configuração inicial concluída.</p></div>', unsafe_allow_html=True)

    with st.container(key="workspace_metrics"):
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            stat_card("Entradas", brl(month_in), detail="Sem lançamentos no mês" if month_tx.empty else "Receitas deste mês", tone="neutral" if month_tx.empty else "positive")
        with m2:
            stat_card("Saídas", brl(month_out), detail="Sem lançamentos no mês" if month_tx.empty else "Despesas deste mês")
        with m3:
            stat_card("Resultado", brl(month_result), detail="Entradas menos saídas", tone="danger" if month_result < 0 else "neutral")
        with m4:
            stat_card("Documentos", str(len(documents)), detail="Seus arquivos organizados")

    with st.container(key="overview_actions"):
        action_a, action_b, action_c = st.columns([1, 1, 2])
        if action_a.button("＋ Movimentação", key="dashboard_new_tx", type="primary", width="stretch"):
            navigate("Movimentações")
        if action_b.button("Importar extrato", key="dashboard_import_statement", width="stretch"):
            navigate("Importar Extrato")

    activity, routine = st.columns([1.8, 1], gap="large")
    with activity:
        with st.container(key="overview_panel_cashflow"):
            st.markdown('<div class="rz-panel-heading"><strong>Seu fluxo financeiro</strong><span>Entradas e saídas no ano</span></div>', unsafe_allow_html=True)
            year_tx = transactions[transactions["tx_date"].dt.year == current_year] if not transactions.empty else transactions
            if year_tx.empty:
                st.markdown(
                    '<div class="rz-financial-empty"><svg viewBox="0 0 100 76" aria-hidden="true" fill="none">'
                    '<rect x="14" y="10" width="65" height="45" rx="8" transform="rotate(-8 14 10)" fill="currentColor" opacity=".12"/>'
                    '<rect x="20" y="22" width="65" height="45" rx="8" fill="var(--rz-surface)" stroke="currentColor" stroke-width="1.5"/>'
                    '<path d="M66 38h19v15H66a7.5 7.5 0 010-15z" fill="var(--rz-primary-soft)" stroke="currentColor" stroke-width="1.5"/>'
                    '<circle cx="71" cy="45.5" r="2" fill="currentColor"/><path d="M31 35h15M31 42h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
                    '<strong>Uma visão clara começa com o primeiro registro.</strong><p>Adicione uma movimentação ou importe seu extrato para acompanhar a evolução do negócio.</p></div>',
                    unsafe_allow_html=True,
                )
            else:
                import plotly.graph_objects as go
                from ui_system import apply_plot_theme
                grouped = year_tx.assign(month=year_tx["tx_date"].dt.month).pivot_table(index="month", columns="tx_type", values="value", aggfunc="sum", fill_value=0).reindex(range(1, 13), fill_value=0)
                figure = go.Figure()
                for kind, color in (("Receita", "#08b9ef"), ("Despesa", "#9bb9cb")):
                    values = grouped[kind] if kind in grouped else [0] * 12
                    figure.add_bar(name="Entradas" if kind == "Receita" else "Saídas", x=[x[:3].lower() for x in month_names], y=values, marker_color=color, marker_cornerradius=4)
                apply_plot_theme(figure, st.session_state.get("ui_theme", "Claro"), height=265)
                figure.update_layout(barmode="group", bargap=.45, legend=dict(orientation="h", y=1.2, x=0), margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})

        with st.container(key="overview_panel_recent"):
            st.markdown('<div class="rz-panel-heading"><strong>Últimas movimentações</strong><span>Seu histórico recente</span></div>', unsafe_allow_html=True)
            if transactions.empty:
                st.markdown('<div class="rz-task-row"><span class="rz-stat-symbol" aria-hidden="true">↔</span><div><strong>Nenhuma movimentação por enquanto</strong><p>As próximas entradas e saídas aparecerão aqui.</p></div></div>', unsafe_allow_html=True)
            else:
                recent = transactions.sort_values("tx_date", ascending=False).head(6).copy()
                recent["Data"] = pd.to_datetime(recent["tx_date"]).dt.date
                recent["Descrição"] = recent["description"].fillna("Sem descrição")
                recent["Tipo"] = recent["tx_type"]
                recent["Valor"] = recent["value"]
                professional_table(recent[["Data", "Descrição", "Tipo", "Valor"]], max_visible_rows=6, column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY"), "Valor": st.column_config.NumberColumn(format="R$ %.2f")})

        with st.container(key="overview_panel_tasks"):
            st.markdown('<div class="rz-panel-heading"><strong>Próximas tarefas</strong><span>Um passo de cada vez</span></div>', unsafe_allow_html=True)
            next_tasks = tasks[1:4] if len(tasks) > 1 else []
            if not next_tasks:
                st.caption("Nenhuma outra tarefa importante por enquanto.")
            for task in next_tasks:
                st.markdown(f'<div class="rz-task-row"><span class="rz-task-check" aria-hidden="true"></span><div><strong>{escape(task["title"])}</strong><p>{escape(task["detail"])}</p></div></div>', unsafe_allow_html=True)

    with routine:
        with st.container(key="overview_panel_limit"):
            ring_percent = min(max(limit_pct, 0), 100)
            offset = 301.593 * (1 - ring_percent / 100)
            percent_label = f"{limit_pct:.1f}%".replace(".", ",") if annual_limit else "—"
            st.markdown(
                f'<div class="rz-panel-heading"><strong>Seu limite MEI</strong><span>{current_year}</span></div>'
                '<div class="rz-limit-content"><div class="rz-limit-ring"><svg viewBox="0 0 108 108" aria-hidden="true">'
                '<circle cx="54" cy="54" r="48" fill="none" stroke="#29485c" stroke-width="5"/>'
                f'<circle cx="54" cy="54" r="48" fill="none" stroke="#08b9ef" stroke-width="5" stroke-linecap="round" stroke-dasharray="301.593" stroke-dashoffset="{offset:.3f}"/></svg><span>{percent_label}</span></div>'
                f'<div class="rz-limit-text"><strong>{brl(annual_revenue)}</strong><p>de {brl(annual_limit)}<br>no ano</p></div></div>'
                '<div class="rz-limit-note">Baseado nas receitas registradas no seu espaço.</div>',
                unsafe_allow_html=True,
            )

        with st.container(key="overview_panel_agenda"):
            st.markdown('<div class="rz-panel-heading"><strong>Sua agenda</strong><span>Próximos 30 dias</span></div>', unsafe_allow_html=True)
            st.caption("PRÓXIMOS VENCIMENTOS")
            if not deadlines:
                st.caption("Nenhum vencimento identificado neste período.")
            for deadline in deadlines[:3]:
                due = deadline["date"]
                st.markdown(
                    f'<div class="rz-agenda-item"><div class="rz-agenda-date"><strong>{due.day:02d}</strong><small>{month_names[due.month - 1][:3]}</small></div>'
                    f'<div class="rz-agenda-info"><strong>{escape(deadline["title"])}</strong><span>{escape(deadline["status"])} · {due.strftime("%d/%m/%Y")}</span></div></div>',
                    unsafe_allow_html=True,
                )
            if st.button("Ver agenda completa  →", key="dashboard_open_obligations", width="stretch"):
                navigate("Obrigações")

        with st.expander("Mais contexto"):
            st.caption(f"Configuração inicial: {setup['percent']}%")
            for index, insight in enumerate(insights[:2]):
                st.markdown(f"**{insight['title']}**")
                st.caption(insight["detail"])
                if st.button("Abrir análise", key=f"dash_insight_{index}"):
                    navigate(insight["page"])
