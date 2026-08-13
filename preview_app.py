from __future__ import annotations

import streamlit as st

# No modo preview, a configuração da página precisa ser o primeiro comando Streamlit.
st.set_page_config(
    page_title="Razync Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import init_db
from preview_access import get_preview_user

# Inicializa o banco e entra automaticamente com o usuário técnico de desenvolvimento.
init_db()
st.session_state.user = get_preview_user()

# Reutiliza todo o app principal, removendo apenas o segundo set_page_config,
# que não pode ser chamado novamente na mesma execução do Streamlit.
with open("app.py", "r", encoding="utf-8") as app_file:
    source = app_file.read()

source = source.replace(
    'st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")\n',
    "",
    1,
)

exec(
    compile(source, "app.py", "exec"),
    {"__name__": "__main__", "__file__": "app.py"},
)
