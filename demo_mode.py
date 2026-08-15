from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ui_system import alert_card, apply_plot_theme, page_header, section


def _brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_demo() -> None:
    """Render a realistic, read-only product preview without database access."""
    theme = st.session_state.get("ui_theme", "Claro")
    st.markdown(
        '<div class="rz-demo-shell"><div class="rz-demo-brand">Razync<span>PRO</span></div><div class="rz-demo-badge">DEMONSTRAÇÃO · DADOS FICTÍCIOS</div></div>',
        unsafe_allow_html=True,
    )
    page_header("Visão geral do seu MEI", "Uma prévia segura de como o Razync organiza financeiro, fiscal e próximas ações.", "Experiência do produto")

    revenue, expenses, balance, limit_used = 18450.0, 6270.0, 12180.0, 22.8
    a, b, c, d = st.columns(4)
    a.metric("Entradas no ano", _brl(revenue))
    b.metric("Saídas no ano", _brl(expenses))
    c.metric("Resultado", _brl(balance))
    d.metric("Limite MEI usado", f"{limit_used:.1f}%")

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
    data = pd.DataFrame({
        "Mês": ["Mar", "Abr", "Mai", "Jun", "Jul", "Ago"],
        "Receitas": [2100, 2800, 2400, 3600, 3350, 4200],
        "Despesas": [900, 760, 1050, 1120, 1180, 1260],
    })
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
        st.dataframe(
            pd.DataFrame([
                {"Obrigação": "DAS · Agosto", "Vencimento": "21/09/2026", "Situação": "Pendente"},
                {"Obrigação": "DAS · Julho", "Vencimento": "20/08/2026", "Situação": "Pago"},
                {"Obrigação": "DASN-SIMEI", "Vencimento": "31/05/2027", "Situação": "Planejado"},
            ]),
            width="stretch", hide_index=True,
        )

    st.caption("Nenhum dado desta demonstração é salvo ou enviado.")
    back, create = st.columns([1, 1])
    if back.button("Voltar para entrar", width="stretch") or create.button("Criar minha conta", type="primary", width="stretch"):
        st.session_state.pop("_demo_mode", None)
        st.rerun()
