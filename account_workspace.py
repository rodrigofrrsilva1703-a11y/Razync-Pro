from __future__ import annotations

import streamlit as st


def render_account_workspace(*, navigate, developer_access: bool) -> None:
    st.caption("SISTEMA E DADOS")
    st.caption("Configurações e dados do Razync em uma área mais simples.")

    a1, a2, spacer = st.columns([1, 1, 1.5], gap="small")
    if a1.button("Dados do MEI", type="primary", width="stretch"):
        navigate("Meu MEI")
    if a2.button("Backup e exportação", width="stretch"):
        navigate("Backup")

    st.markdown("#### Gestão do sistema")
    with st.container(key="rz_panel_account_system"):
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("**Integrações**")
            st.caption("Serviços conectados e recursos externos.")
            if st.button("Abrir integrações", key="account_integrations", width="stretch"):
                navigate("Integrações")
        with right:
            st.markdown("**Histórico de atividades**")
            st.caption("Inclusões, alterações e exclusões registradas.")
            if st.button("Abrir histórico", key="account_history", width="stretch"):
                navigate("Histórico de Atividades")

    with st.expander("Mais configurações"):
        b1, b2 = st.columns(2)
        if b1.button("Status do sistema", width="stretch"):
            navigate("Status do Sistema")
        if b2.button("Planos e recursos", width="stretch"):
            navigate("Plano e Assinatura")

    with st.expander("Dados e privacidade"):
        st.markdown("**Exportação** · disponível")
        st.caption("Use o Backup para gerar uma cópia do workspace.")
        st.markdown("**Correção de dados** · disponível")
        st.caption("Cadastros e movimentações podem ser atualizados no próprio sistema.")
        st.markdown("**Contas individuais** · temporariamente desativadas")
        st.caption("Login e isolamento por usuário voltam quando a autenticação for reativada.")
