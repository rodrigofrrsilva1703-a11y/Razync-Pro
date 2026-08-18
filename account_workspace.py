from __future__ import annotations

import streamlit as st

from commercial_readiness import PLAN_CATALOG, data_rights_summary


def render_account_workspace(*, navigate, developer_access: bool) -> None:
    st.caption("CONTA, PRIVACIDADE E SISTEMA")
    st.write("Centralize dados do MEI, segurança, plano, histórico e cópias dos seus dados.")

    a, b, c = st.columns(3)
    with a:
        with st.container(border=True):
            st.markdown("**Dados e segurança**")
            st.caption("Cadastro do MEI, senha e proteção da conta.")
            if st.button("Dados do MEI", key="account_mei", width="stretch"):
                navigate("Meu MEI")
            if st.button("Segurança", key="account_security", width="stretch"):
                navigate("Segurança da Conta")
    with b:
        with st.container(border=True):
            st.markdown("**Dados e privacidade**")
            st.caption("Histórico, backup e direitos sobre seus dados.")
            if st.button("Histórico", key="account_history", width="stretch"):
                navigate("Histórico de Atividades")
            if st.button("Backup / exportação", key="account_backup", width="stretch"):
                navigate("Backup")
    with c:
        with st.container(border=True):
            st.markdown("**Operação**")
            st.caption("Integrações, infraestrutura e assinatura.")
            if st.button("Integrações", key="account_integrations", width="stretch"):
                navigate("Integrações")
            if st.button("Status do sistema", key="account_status", width="stretch"):
                navigate("Status do Sistema")

    st.subheader("Plano")
    current = "Pro" if developer_access else "Essencial"
    plan = PLAN_CATALOG[current]
    st.info(f"Plano atual: {current} — {plan['description']}")
    if st.button("Ver plano e assinatura", key="account_plan", width="stretch"):
        navigate("Plano e Assinatura")

    st.subheader("Seus direitos sobre os dados")
    for item in data_rights_summary():
        with st.container(border=True):
            st.markdown(f"**{item['title']}** · {item['status']}")
            st.caption(item["detail"])
