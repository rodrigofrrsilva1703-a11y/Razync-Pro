from __future__ import annotations

import streamlit as st

from compact_cards import navigation_card


def render_account_workspace(*, navigate, developer_access: bool) -> None:
    st.caption("SISTEMA E DADOS")
    st.caption("Configurações, integrações, histórico e exportações em um só lugar.")

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

    st.markdown("#### Produto")
    st.caption("O ambiente atual está em acesso direto para desenvolvimento e não possui uma assinatura individual vinculada.")
    if navigation_card(
        "Ver planos e recursos",
        key="account_plan",
        help_text="Comparar os recursos previstos para cada plano",
    ):
        navigate("Plano e Assinatura")

    with st.expander("Dados e privacidade"):
        st.markdown("**Exportar dados** · disponível")
        st.caption("Use o Backup para gerar uma cópia dos dados e documentos do workspace.")
        st.markdown("**Corrigir dados** · disponível")
        st.caption("Dados do MEI, movimentações e demais registros podem ser atualizados no sistema.")
        st.markdown("**Contas individuais** · temporariamente desativadas")
        st.caption("Login, isolamento por usuário e exclusão de conta voltam a ser tratados quando a autenticação for reativada.")
