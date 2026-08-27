from __future__ import annotations

import streamlit as st


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
            with st.container(border=True):
                st.markdown(f"**{title}**")
                if st.button("Abrir  →", key=f"productivity_{page}", width="stretch", help=detail):
                    navigate(page)
