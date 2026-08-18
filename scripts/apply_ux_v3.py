from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)

app_path = Path("app.py")
app = app_path.read_text(encoding="utf-8")

app = replace_once(
    app,
    "from navigation_config import SIDEBAR_LABELS, SIDEBAR_GROUPS, SIDEBAR_SECONDARY_GROUPS, SIDEBAR_ICONS\n",
    "from navigation_config import SIDEBAR_LABELS, SIDEBAR_GROUPS, SIDEBAR_SECONDARY_GROUPS, SIDEBAR_ICONS\n"
    "from finance_workspace import render_finance_workspace\n"
    "from fiscal_workspace import render_fiscal_workspace\n"
    "from workspace_style import inject_workspace_style\n",
    "workspace imports",
)

app = replace_once(
    app,
    "inject_design_system(UI_THEME)\n",
    "inject_design_system(UI_THEME)\ninject_workspace_style()\n",
    "workspace style",
)

app = replace_once(
    app,
    "def alert_box(level: str, title: str, text: str) -> None:\n    alert_card(level, title, text)\n\n\n",
    "def alert_box(level: str, title: str, text: str) -> None:\n    alert_card(level, title, text)\n\n\n"
    "def navigate_to(destination: str) -> None:\n"
    "    st.session_state[\"_navigate_to\"] = destination\n"
    "    st.rerun()\n\n\n",
    "navigate helper",
)

finance_branch = '''elif page == "Financeiro":\n    header("Financeiro", "Controle entradas, saídas, conciliação e análise em uma única área.")\n    render_finance_workspace(\n        transactions=transactions,\n        invoices=invoices,\n        annual_limit=limit,\n        current_year=CURRENT_YEAR,\n        theme=UI_THEME,\n        brl=brl,\n        navigate=navigate_to,\n    )\n\n'''
app = replace_once(app, 'elif page == "Movimentações":\n', finance_branch + 'elif page == "Movimentações":\n', "finance page")

fiscal_branch = '''elif page == "Fiscal":\n    header("Fiscal MEI", "Acompanhe DAS, notas, obrigações e declaração anual sem se perder entre telas.")\n    render_fiscal_workspace(\n        profile=profile,\n        transactions=transactions,\n        invoices=invoices,\n        das_rows=das_rows,\n        obligations=obligations,\n        documents=docs,\n        current_year=CURRENT_YEAR,\n        annual_limit=limit,\n        annual_revenue=year_revenue,\n        brl=brl,\n        navigate=navigate_to,\n    )\n\n'''
app = replace_once(app, 'elif page == "DAS":\n', fiscal_branch + 'elif page == "DAS":\n', "fiscal page")

app_path.write_text(app, encoding="utf-8")

product_path = Path("product_core.py")
product = product_path.read_text(encoding="utf-8")
product = replace_once(
    product,
    '    "Financeiro": ["Movimentações", "Recorrências", "Importar Extrato", "Conciliação", "Fluxo de Caixa", "Análise Financeira"],\n',
    '    "Financeiro": ["Financeiro", "Movimentações", "Recorrências", "Importar Extrato", "Conciliação", "Fluxo de Caixa", "Análise Financeira"],\n',
    "finance route",
)
product = replace_once(
    product,
    '    "Fiscal MEI": ["DAS", "DASN-SIMEI", "Obrigações", "Notas Fiscais", "Importar NFS-e", "Relatório Mensal", "Fechamento Mensal"],\n',
    '    "Fiscal MEI": ["Fiscal", "DAS", "DASN-SIMEI", "Obrigações", "Notas Fiscais", "Importar NFS-e", "Relatório Mensal", "Fechamento Mensal"],\n',
    "fiscal route",
)
product_path.write_text(product, encoding="utf-8")

print("UX V3 workspaces integrated")
