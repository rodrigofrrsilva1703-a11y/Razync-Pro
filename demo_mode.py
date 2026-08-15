from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ui_system import alert_card, apply_plot_theme, page_header, section


def _brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _leave_demo() -> None:
    """Return to authentication without keeping demo-only navigation state."""
    st.session_state.pop("_demo_mode", None)
    st.session_state.pop("_demo_section", None)
    st.rerun()


def _demo_sidebar() -> str:
    """Keep the product navigation visible while using the public preview."""
    with st.sidebar:
        st.markdown(
            '<div class="rz-brand-wrap"><div class="rz-brand">Razync<span>PRO</span></div>'
            '<div class="rz-brand-sub">Demonstração segura</div></div>',
            unsafe_allow_html=True,
        )
        st.caption("Explore o sistema com dados fictícios.")
        section = st.session_state.get("_demo_section", "Visão geral")
        destinations = {
            "Visão geral": ":material/home:",
            "Financeiro": ":material/account_balance_wallet:",
            "Automações": ":material/automation:",
            "Fiscal e DAS": ":material/receipt_long:",
        }
        for destination, icon in destinations.items():
            if st.button(
                destination,
                key=f"demo_nav_{destination}",
                icon=icon,
                disabled=section == destination,
                width="stretch",
            ):
                st.session_state["_demo_section"] = destination
                st.rerun()
        st.divider()
        st.caption("Para usar seus dados reais, entre na sua conta.")
        if st.button("Entrar no sistema", type="primary", width="stretch"):
            _leave_demo()
    return section


def render_demo() -> None:
    """Render a realistic, read-only product preview without database access."""
    theme = st.session_state.get("ui_theme", "Claro")
    demo_section = _demo_sidebar()
    st.markdown(
        '<div class="rz-demo-shell"><div class="rz-demo-brand">Razync<span>PRO</span></div><div class="rz-demo-badge">DEMONSTRAÇÃO · DADOS FICTÍCIOS</div></div>',
        unsafe_allow_html=True,
    )
    subtitles = {
        "Visão geral": "Uma prévia segura de como o Razync organiza financeiro, fiscal e próximas ações.",
        "Financeiro": "Acompanhe receitas, despesas e resultado sem depender de planilhas.",
        "Automações": "Veja tarefas que o sistema identifica e deixa prontas para sua confirmação.",
        "Fiscal e DAS": "Centralize vencimentos e acompanhe suas principais obrigações do MEI.",
    }
    page_header(demo_section, subtitles[demo_section], "Experiência do produto")

    revenue, expenses, balance, limit_used = 18450.0, 6270.0, 12180.0, 22.8
    data = pd.DataFrame({
        "Mês": ["Mar", "Abr", "Mai", "Jun", "Jul", "Ago"],
        "Receitas": [2100, 2800, 2400, 3600, 3350, 4200],
        "Despesas": [900, 760, 1050, 1120, 1180, 1260],
    })

    if demo_section in {"Visão geral", "Financeiro"}:
        a, b, c, d = st.columns(4)
        a.metric("Entradas no ano", _brl(revenue))
        b.metric("Saídas no ano", _brl(expenses))
        c.metric("Resultado", _brl(balance))
        d.metric("Limite MEI usado", f"{limit_used:.1f}%")

    if demo_section == "Visão geral":
        action_col, status_col = st.columns([1.65, 1], gap="large")
        with action_col:
            section("Próximo passo recomendado", "O Razync prioriza o que merece sua atenção.")
            st.markdown('<div class="rz-next-action"><strong>Conferir o DAS de agosto</strong><span>Vencimento fictício em 21/09/2026. O pagamento ainda não foi identificado no extrato.</span></div>', unsafe_allow_html=True)
        with status_col:
            section("Saúde do MEI", "Indicadores explicados, sem termos complicados.")
            st.progress(limit_used / 100)
            st.caption("Faturamento dentro do limite monitorado")
            st.progress(0.86)
            st.caption("Organização dos documentos: 86%")

        overview_tab, automation_tab, fiscal_tab = st.tabs(["Financeiro", "Automações", "Fiscal"])
        with overview_tab:
            section("Evolução financeira", "Receitas e despesas fictícias dos últimos seis meses.")
            fig = px.area(data, x="Mês", y=["Receitas", "Despesas"], markers=True, color_discrete_sequence=["#08b9ef", "#607487"])
            apply_plot_theme(fig, theme, height=310)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        with automation_tab:
            alert_card("warn", "1 tarefa pede confirmação", "O sistema encontrou um possível pagamento de DAS no extrato.")
            alert_card("info", "2 conciliações sugeridas", "Notas e recebimentos parecidos estão prontos para você revisar.")
            alert_card("ok", "Previsão positiva", "O saldo projetado permanece positivo nos próximos três meses.")
        with fiscal_tab:
            _render_fiscal_preview()
    elif demo_section == "Financeiro":
        section("Evolução financeira", "Receitas e despesas fictícias dos últimos seis meses.")
        fig = px.area(data, x="Mês", y=["Receitas", "Despesas"], markers=True, color_discrete_sequence=["#08b9ef", "#607487"])
        apply_plot_theme(fig, theme, height=310)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    elif demo_section == "Automações":
        alert_card("warn", "1 tarefa pede confirmação", "O sistema encontrou um possível pagamento de DAS no extrato.")
        alert_card("info", "2 conciliações sugeridas", "Notas e recebimentos parecidos estão prontos para você revisar.")
        alert_card("ok", "Previsão positiva", "O saldo projetado permanece positivo nos próximos três meses.")
    else:
        _render_fiscal_preview()

    st.caption("Nenhum dado desta demonstração é salvo ou enviado.")
    back, create = st.columns([1, 1])
    if back.button("Voltar para entrar", width="stretch") or create.button("Criar minha conta", type="primary", width="stretch"):
        _leave_demo()


def _render_fiscal_preview() -> None:
    st.dataframe(
        pd.DataFrame([
            {"Obrigação": "DAS · Agosto", "Vencimento": "21/09/2026", "Situação": "Pendente"},
            {"Obrigação": "DAS · Julho", "Vencimento": "20/08/2026", "Situação": "Pago"},
            {"Obrigação": "DASN-SIMEI", "Vencimento": "31/05/2027", "Situação": "Planejado"},
        ]),
        width="stretch", hide_index=True,
    )
