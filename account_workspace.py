from __future__ import annotations

import streamlit as st

from account_deletion import AccountDeletionError, delete_account
from commercial_readiness import PLAN_CATALOG, data_rights_summary
from monitoring import safe_error
from session_persistence import clear_persisted_session, persistent_session_controller


def _finish_deleted_session() -> None:
    controller = persistent_session_controller()
    if controller is not None:
        clear_persisted_session(controller)
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


def render_account_workspace(*, navigate, developer_access: bool) -> None:
    st.caption("CONTA, PRIVACIDADE E SISTEMA")
    st.caption("Dados do MEI, segurança, plano e privacidade em um só lugar.")

    a, b, c = st.columns(3)
    with a:
        with st.container(border=True):
            st.markdown("**Dados e segurança**")
            st.caption("Cadastro e proteção da conta.")
            if st.button("Dados do MEI", key="account_mei", width="stretch"):
                navigate("Meu MEI")
            if st.button("Segurança", key="account_security", width="stretch"):
                navigate("Segurança da Conta")
    with b:
        with st.container(border=True):
            st.markdown("**Dados e privacidade**")
            st.caption("Histórico, backup e direitos.")
            if st.button("Histórico", key="account_history", width="stretch"):
                navigate("Histórico de Atividades")
            if st.button("Backup / exportação", key="account_backup", width="stretch"):
                navigate("Backup")
    with c:
        with st.container(border=True):
            st.markdown("**Operação**")
            st.caption("Integrações e assinatura.")
            if st.button("Integrações", key="account_integrations", width="stretch"):
                navigate("Integrações")
            if st.button("Status do sistema", key="account_status", width="stretch"):
                navigate("Status do Sistema")

    st.markdown("#### Plano")
    current = "Pro" if developer_access else "Essencial"
    plan = PLAN_CATALOG[current]
    st.info(f"Plano atual: {current} — {plan['description']}")
    if st.button("Ver plano e assinatura", key="account_plan", width="stretch"):
        navigate("Plano e Assinatura")

    with st.expander("Seus direitos sobre os dados"):
        for item in data_rights_summary():
            st.markdown(f"**{item['title']}** · {item['status']}")
            st.caption(item["detail"])

    st.markdown("#### Excluir conta")
    access_token = str(st.session_state.get("access_token") or "")
    if developer_access:
        st.info("O acesso de desenvolvedor via GitHub não é uma conta de cliente Supabase e não pode ser excluído por esta tela.")
    elif not access_token:
        st.warning("Valide sua sessão novamente para disponibilizar a exclusão da conta.")
    else:
        with st.expander("Excluir permanentemente minha conta e meus dados"):
            st.warning(
                "Esta ação remove os dados do Razync, os documentos privados e a identidade de acesso. "
                "Faça um backup antes se quiser guardar uma cópia."
            )
            confirmation = st.text_input(
                'Digite exatamente "EXCLUIR MINHA CONTA" para confirmar',
                key="account_delete_confirmation",
            )
            acknowledged = st.checkbox(
                "Entendo que a exclusão é permanente.",
                key="account_delete_acknowledged",
            )
            ready = confirmation.strip() == "EXCLUIR MINHA CONTA" and acknowledged
            if st.button(
                "Excluir minha conta permanentemente",
                key="account_delete_button",
                type="primary",
                width="stretch",
                disabled=not ready,
            ):
                try:
                    delete_account(access_token)
                except AccountDeletionError as exc:
                    safe_error("account_delete_failed", exc, operation="delete_account", backend="supabase_edge")
                    st.error(str(exc))
                else:
                    st.success("Conta excluída. Encerrando a sessão com segurança.")
                    _finish_deleted_session()
