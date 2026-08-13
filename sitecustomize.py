"""Ajustes de runtime do Razync Pro.

O Streamlit Community Cloud executa o projeto em um ambiente efêmero. Quando
nenhum PostgreSQL foi configurado, usamos um SQLite em /tmp para evitar erro de
permissão na pasta do repositório. Em produção, basta definir DATABASE_URL e o
PostgreSQL terá prioridade.
"""

from __future__ import annotations

import os


if not os.getenv("DATABASE_URL"):
    # /tmp é gravável no Streamlit Community Cloud.
    os.environ["DATABASE_URL"] = "sqlite:////tmp/razync_pro.db"
