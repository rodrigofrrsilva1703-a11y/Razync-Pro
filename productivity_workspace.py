from __future__ import annotations

import streamlit as st

from compact_cards import navigation_card


def render_productivity_workspace(*, navigate) -> None:
    st.caption("AUTOMAÇÃO E PRODUTIVIDADE")
    st.caption("Recursos inteligentes em uma única área. Ações externas sempre pedem confirmação.")
    cards = [
        ("Automações", "Fechamento, conciliação, previsões e rotinas assistidas.", "Central de Automações"),
        ("Alertas e calendário", "Pendências, vencimentos e arquivo de calendário.", "Central de Notificações"),
    ]
    columns = st.columns(3)
    for column, (title, detail, page) in zip(columns[:2], cards):
        with column:
            if navigation_card(title, key=f"productivity_{page}", help_text=detail):
                navigate(page)

    with columns[2]:
        if navigation_card(
            "Razync IA",
            key="productivity_floating_ai",
            help_text="Abrir o assistente flutuante sem sair desta ferramenta.",
        ):
            st.session_state["razync_ai_pending_question"] = "Como você pode me ajudar a organizar minhas rotinas e prioridades agora?"
            st.session_state["razync_floating_open"] = True
            st.rerun()
