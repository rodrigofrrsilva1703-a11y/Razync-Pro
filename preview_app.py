from __future__ import annotations

import streamlit as st

from database import init_db
from preview_access import get_preview_user

# Entrada direta para desenvolvimento e acompanhamento das atualizações.
# O app principal continua preservado para reativarmos autenticação na produção pública.
init_db()
st.session_state.user = get_preview_user()

with open("app.py", "r", encoding="utf-8") as app_file:
    source = app_file.read()

exec(compile(source, "app.py", "exec"), {"__name__": "__main__", "__file__": "app.py"})
