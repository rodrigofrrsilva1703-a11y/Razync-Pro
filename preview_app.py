from __future__ import annotations

# O preview executa exatamente o mesmo app principal.
# A única diferença é substituir a chamada de login por um usuário técnico automático.
with open("app.py", "r", encoding="utf-8") as app_file:
    source = app_file.read()

# Importa o helper de preview dentro do app executado.
source = source.replace(
    "from reports import dasn_summary_pdf, monthly_report_pdf\n",
    "from reports import dasn_summary_pdf, monthly_report_pdf\nfrom preview_access import get_preview_user\n",
    1,
)

# Pula somente a tela de login, preservando todo o restante do app.py.
source = source.replace(
    "user = ensure_login()\n",
    "user = get_preview_user()\n",
    1,
)

exec(
    compile(source, "app.py", "exec"),
    {"__name__": "__main__", "__file__": "app.py"},
)
