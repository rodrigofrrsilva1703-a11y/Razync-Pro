from pathlib import Path

app = Path('app.py')
ui = Path('ui_system.py')
s = app.read_text(encoding='utf-8')
u = ui.read_text(encoding='utf-8')

# Replace the legacy two-level radio sidebar with direct expandable navigation.
start = s.index('pending_page = st.session_state.pop("_navigate_to", None)')
end = s.index('\nopening = opening_date_from(profile)', start)
nav = '''pending_page = st.session_state.pop("_navigate_to", None)
if pending_page:
    st.session_state["_current_page"] = pending_page

page = st.session_state.get("_current_page", "Dashboard")
all_pages = [p for pages in NAV_GROUPS.values() for p in pages]
if page not in all_pages:
    page = "Dashboard"
    st.session_state["_current_page"] = page

with st.sidebar:
    st.markdown('<div class="rz-brand-wrap"><div class="rz-brand">RAZYNC <span>PRO</span></div><div class="rz-brand-sub">Contabilidade simples para MEI</div></div>', unsafe_allow_html=True)
    st.selectbox("Tema", ["Claro", "Escuro"], key="ui_theme")
    st.markdown('<div class="rz-sidebar-section">Navegação</div>', unsafe_allow_html=True)

    if page == "Dashboard":
        st.markdown('<div class="rz-current-page">⌂  Início</div>', unsafe_allow_html=True)
    elif st.button("⌂  Início", key="nav_home", use_container_width=True):
        st.session_state["_navigate_to"] = "Dashboard"
        st.rerun()

    sidebar_groups = {
        "Financeiro": NAV_GROUPS["Financeiro"],
        "Fiscal MEI": NAV_GROUPS["Fiscal MEI"],
        "Gestão": NAV_GROUPS["Gestão"],
        "Relatórios": NAV_GROUPS["Relatórios"],
        "Configurações": NAV_GROUPS["Configurações"],
    }
    icons = {"Financeiro":"▰", "Fiscal MEI":"▣", "Gestão":"◇", "Relatórios":"▤", "Configurações":"⚙"}
    current_group = group_for_page(page)
    for group, pages in sidebar_groups.items():
        with st.expander(f"{icons[group]}  {group}", expanded=(current_group == group)):
            for nav_page in pages:
                if nav_page == page:
                    st.markdown(f'<div class="rz-current-page">{nav_page}</div>', unsafe_allow_html=True)
                elif st.button(nav_page, key=f"nav_{group}_{nav_page}", use_container_width=True):
                    st.session_state["_navigate_to"] = nav_page
                    st.rerun()
    st.markdown('<div class="rz-dev">Desenvolvimento • acesso direto</div>', unsafe_allow_html=True)
'''
s = s[:start] + nav + s[end:]

# Add a stronger dark override layer to neutralize the light native Streamlit base.
marker = '    st.markdown(\n        f"""\n<style>'
if marker not in u:
    raise RuntimeError('design system marker not found')

insert_point = u.index(marker)
if 'dark_overrides = ' not in u:
    dark_block = '''    dark_overrides = "" if theme_name != "Escuro" else """
/* Dark theme owns all native Streamlit surfaces; no light-base leakage. */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#0c1424 !important; color:#e7edf7 !important; }
[data-testid="stHeader"] { background:#0c1424 !important; border-bottom:1px solid #25344c !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#111c2e !important; border-right-color:#263750 !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { color:#91a3bb !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#162238 !important; border-color:#2b3d59 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#17243a !important; color:#e7edf7 !important; border-color:#334764 !important; box-shadow:none !important; }
[data-baseweb="select"] > div > div, [data-baseweb="input"] > div > div { background:transparent !important; color:#e7edf7 !important; }
[data-baseweb="select"] svg, [data-baseweb="input"] svg { color:#9fb0c6 !important; fill:#9fb0c6 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#17243a !important; color:#e7edf7 !important; border-color:#334764 !important; }
[role="option"]:hover { background:#20314d !important; }
button:not([kind="primary"]) { background:#17243a !important; color:#dce6f3 !important; border-color:#334764 !important; box-shadow:none !important; }
button:not([kind="primary"]):hover { background:#20314d !important; color:#7fb2ff !important; border-color:#4b6f9f !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:#1b2c46 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#1b2c46 !important; }
[data-testid="stFileUploaderDropzone"] { background:#142137 !important; border-color:#334764 !important; }
[data-testid="stFileUploaderDropzone"] * { color:#aebed2 !important; }
[data-testid="stTabs"] button { color:#94a7bf !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#79aef8 !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p, label, p, span { color:#d9e3ef !important; }
h1,h2,h3,h4,h5,h6 { color:#f2f6fb !important; }
small,[data-testid="stCaptionContainer"],.stCaption { color:#93a5bc !important; }
[data-testid="stAlert"] { background:#1a2a43 !important; }
[data-testid="stAlert"] p { color:#dce6f3 !important; }
[data-testid="stProgressBar"] > div { background:#23334b !important; }
[data-testid="stProgressBar"] > div > div { background:#4f8ee8 !important; }
[data-testid="stNumberInput"] button { background:#162238 !important; color:#a9bad0 !important; border-color:#334764 !important; }
[data-testid="stNumberInput"] button:hover { background:#20314d !important; }
[data-testid="stRadio"] [role="radiogroup"] label div:first-child { background:#17243a !important; border-color:#50647f !important; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div:first-child { background:#4f8ee8 !important; border-color:#7fb2ff !important; }
.rz-current-page { background:#1e3a63 !important; color:#8fc0ff !important; }
.rz-dev { background:#142137 !important; border-color:#2b3d59 !important; color:#8fa2ba !important; }
hr { border-color:#263750 !important; }
"""
'''
    u = u[:insert_point] + dark_block + u[insert_point:]

# Ensure dark overrides are emitted after generic CSS/light overrides.
u = u.replace('{light_overrides}\n@media', '{light_overrides}\n{dark_overrides}\n@media', 1)

app.write_text(s, encoding='utf-8')
ui.write_text(u, encoding='utf-8')
print('sidebar and dark theme v4 applied')
