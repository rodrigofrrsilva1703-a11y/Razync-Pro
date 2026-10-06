from __future__ import annotations

import streamlit as st

from account_deletion import AccountDeletionError, delete_account
from commercial_readiness import PLAN_CATALOG, data_rights_summary
from monitoring import safe_error
from session_persistence import clear_persisted_session, persistent_session_controller
from compact_cards import navigation_card


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

    tools = (
        ("Dados do MEI", "Meu MEI", "Cadastro e informações do negócio"),
        ("Histórico", "Histórico de Atividades", "Ações registradas no sistema"),
        ("Backup e exportação", "Backup", "Baixar uma cópia dos seus dados"),
        ("Integrações", "Integrações", "Recursos e serviços conectados"),
        ("Status do sistema", "Status do Sistema", "Saúde dos serviços do Razync"),
    )
    columns = st.columns(3)
    for index, (label, page, help_text) in enumerate(tools):
        with columns[index % 3]:
            if navigation_card(label, key=f"account_{index}", help_text=help_text):
                navigate(page)

    st.markdown("#### Plano")
    current = "Pro" if developer_access else "Essencial"
    plan = PLAN_CATALOG[current]
    st.info(f"Plano atual: {current} — {plan['description']}")
    if navigation_card("Ver plano e assinatura", key="account_plan", help_text="Detalhes do plano atual"):
        navigate("Plano e Assinatura")

    with st.expander("Seus direitos sobre os dados"):
        for item in data_rights_summary():
            st.markdown(f"**{item['title']}** · {item['status']}")
            st.caption(item["detail"])

    st.info("O Razync está temporariamente em modo de acesso direto. Login, senha e exclusão de conta ficam ocultos até a autenticação ser reativada.")
