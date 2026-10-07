from __future__ import annotations

import streamlit as st


def render_productivity_workspace(*, navigate) -> None:
    left, right = st.columns(2, gap="large")
    with left, st.container(key="rz_panel_productivity_automation"):
        st.caption("AUTOMAÇÕES")
        st.markdown("**Rotinas assistidas**")
        st.write("Fechamento, conciliação, previsões e tarefas recorrentes.")
        if st.button("Abrir automações", type="primary", width="stretch"):
            navigate("Central de Automações")

    with right, st.container(key="rz_panel_productivity_alerts"):
        st.caption("ALERTAS")
        st.markdown("**Prazos e calendário**")
        st.write("Pendências, vencimentos e agenda do MEI.")
        if st.button("Abrir alertas", width="stretch"):
            navigate("Central de Notificações")

    st.caption("Precisa de ajuda com alguma rotina? Converse com o Razync IA pelo botão no canto da tela.")
