from __future__ import annotations

import streamlit as st

from compact_cards import navigation_card


def render_productivity_workspace(*, navigate) -> None:
    st.caption("AUTOMAÇÃO E PRODUTIVIDADE")
    st.caption("Recursos inteligentes em uma única área. Ações externas sempre pedem confirmação.")
    cards = [
        ("Automações", "Fechamento, conciliação, previsões e rotinas assistidas.", "Central de Automações"),
        ("Alertas e calendário", "Pendências, vencimentos e arquivo de calendário.", "Central de Notificações"),
        ("Assistente Razync", "Perguntas em linguagem simples usando os dados já cadastrados.", "Assistente Razync"),
    ]
    columns = st.columns(3)
    for column, (title, detail, page) in zip(columns, cards):
        with column:
            if navigation_card(title, key=f"productivity_{page}", help_text=detail):
                navigate(page)
