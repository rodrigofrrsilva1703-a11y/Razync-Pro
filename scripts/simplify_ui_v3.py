from pathlib import Path

app_path = Path('app.py')
ui_path = Path('ui_system.py')
s = app_path.read_text(encoding='utf-8')
u = ui_path.read_text(encoding='utf-8')

u = u.replace('"bg": "#f4f7fb",', '"bg": "#f7f9fc",')
u = u.replace('"surface_soft": "#f8fafc",', '"surface_soft": "#f1f5f9",')
u = u.replace('"text": "#0f172a",', '"text": "#111827",')
u = u.replace('"muted": "#64748b",', '"muted": "#526071",')
u = u.replace('"border": "#dfe6ef",', '"border": "#d9e2ec",')
u = u.replace('"primary_soft": "#eff6ff",', '"primary_soft": "#e8f1ff",')

insert_after = 'small,[data-testid="stCaptionContainer"],.stCaption {{ color:var(--rz-muted)!important; }}\n'
extra = '''
/* Explicit color ownership prevents Streamlit dark defaults leaking into light theme */
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label {{ color:var(--rz-text)!important; }}
[data-testid="stSidebar"] small,[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:var(--rz-muted)!important; }}
[data-testid="stSidebar"] [data-baseweb="base-input"], [data-testid="stSidebar"] [data-baseweb="select"] > div {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; }}
[data-testid="stSidebar"] svg {{ fill:currentColor; color:var(--rz-muted); }}
[data-testid="stAlert"] {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; border-color:var(--rz-border)!important; }}
[data-testid="stAlert"] p {{ color:var(--rz-text)!important; }}
[data-testid="stMarkdownContainer"] a {{ color:var(--rz-primary)!important; }}
[data-testid="stWidgetLabel"] p {{ color:var(--rz-text)!important; }}
'''
if extra.strip() not in u and insert_after in u:
    u = u.replace(insert_after, insert_after + extra, 1)

nav_marker = '/* Sidebar navigation */\n'
nav_extra = '''
.rz-sidebar-section {{ font-size:.67rem; font-weight:800; text-transform:uppercase; letter-spacing:.09em; color:var(--rz-muted); margin:.8rem .15rem .32rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] {{ box-shadow:none; border:0; background:transparent; border-radius:10px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] details {{ border:0; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{ border-radius:9px; padding:.32rem .4rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{ background:var(--rz-soft); }}
[data-testid="stSidebar"] [data-testid="stButton"] button {{ width:100%; min-height:2.25rem; text-align:left; justify-content:flex-start; padding:.35rem .65rem; border:0; background:transparent; box-shadow:none; }}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{ background:var(--rz-primary-soft); color:var(--rz-primary); }}
.rz-current-page {{ background:var(--rz-primary-soft); color:var(--rz-primary); border-radius:9px; padding:.55rem .7rem; font-weight:760; font-size:.86rem; margin-bottom:.3rem; }}
'''
if nav_extra.strip() not in u and nav_marker in u:
    u = u.replace(nav_marker, nav_marker + nav_extra, 1)

ui_path.write_text(u, encoding='utf-8')

nav_start = s.index('pending_page = st.session_state.pop("_navigate_to", None)')
nav_end = s.index('\nopening = opening_date_from(profile)', nav_start)
new_nav = '''pending_page = st.session_state.pop("_navigate_to", None)
if pending_page:
    st.session_state["_current_page"] = pending_page

page = st.session_state.get("_current_page", "Dashboard")
all_pages = [p for pages in NAV_GROUPS.values() for p in pages]
if page not in all_pages:
    page = "Dashboard"
    st.session_state["_current_page"] = page

with st.sidebar:
    st.markdown('<div class="rz-brand-wrap"><div class="rz-brand">RAZYNC <span>PRO</span></div><div class="rz-brand-sub">Gestão contábil para MEI</div></div>', unsafe_allow_html=True)
    st.radio("Aparência", ["Claro", "Escuro"], horizontal=True, key="ui_theme")
    st.markdown('<div class="rz-sidebar-section">Navegação</div>', unsafe_allow_html=True)

    if page == "Dashboard":
        st.markdown('<div class="rz-current-page">⌂  Início</div>', unsafe_allow_html=True)
    elif st.button("⌂  Início", key="nav_home", use_container_width=True):
        st.session_state["_navigate_to"] = "Dashboard"; st.rerun()

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
                    st.session_state["_navigate_to"] = nav_page; st.rerun()
    st.markdown('<div class="rz-dev">Desenvolvimento • acesso direto</div>', unsafe_allow_html=True)
'''
s = s[:nav_start] + new_nav + s[nav_end:]

dashboard_anchor = s.index('limit_pct = (year_revenue/limit*100) if limit else 0.0')
dash_start = s.index('\nif page == "Dashboard":', dashboard_anchor) + 1
dash_end = s.index('\nelif page == "Movimentações":', dash_start)
new_dashboard = '''if page == "Dashboard":
    business_label = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"
    cnpj_label = str(profile.get("cnpj") or "").strip() or None
    page_header("Início", "O essencial do seu MEI, sem excesso de informação.")
    business_card(business_label, CURRENT_YEAR, cnpj_label)

    today = date.today()
    month_tx = transactions[(transactions["tx_date"].dt.year == CURRENT_YEAR) & (transactions["tx_date"].dt.month == today.month)] if not transactions.empty else transactions
    month_in = float(month_tx[month_tx["tx_type"] == "Receita"]["value"].sum()) if not month_tx.empty else 0.0
    month_out = float(month_tx[month_tx["tx_type"] == "Despesa"]["value"].sum()) if not month_tx.empty else 0.0
    month_result = month_in - month_out

    section("Seu mês")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Entradas", brl(month_in))
    k2.metric("Saídas", brl(month_out))
    k3.metric("Resultado", brl(month_result))
    k4.metric("Limite MEI usado", f"{limit_pct:.1f}%")

    priorities = action_items(profile, transactions, invoices, das_rows, obligations, limit, year_revenue)
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        section("Próximas ações", "O que merece atenção primeiro.")
        for idx, item in enumerate(priorities[:2]):
            row, btn = st.columns([4.5,1.2])
            with row:
                level = "danger" if item["priority"] == 1 else "warn" if item["priority"] == 2 else "info" if item["priority"] == 3 else "ok"
                alert_card(level, item["title"], item["detail"])
            with btn:
                if item["page"] != "Dashboard" and st.button("Resolver", key=f"home_priority_{idx}", use_container_width=True):
                    st.session_state["_navigate_to"] = item["page"]; st.rerun()
    with right:
        section("Ações rápidas")
        if st.button("＋ Nova movimentação", key="home_tx", use_container_width=True):
            st.session_state["_navigate_to"] = "Movimentações"; st.rerun()
        if st.button("↥ Importar extrato", key="home_import", use_container_width=True):
            st.session_state["_navigate_to"] = "Importar Extrato"; st.rerun()
        if st.button("▣ Central Fiscal", key="home_fiscal", use_container_width=True):
            st.session_state["_navigate_to"] = "Central Fiscal"; st.rerun()

    overdue_das = sum(1 for d in das_rows if das_status(d.get("status", "Pendente"), d.get("due_date")) == "Atrasado")
    remaining = max(limit - year_revenue, 0)
    st.caption(f"Faturamento no ano: {brl(year_revenue)}  •  Limite restante: {brl(remaining)}  •  DAS em atraso: {overdue_das}")
'''
s = s[:dash_start] + new_dashboard + s[dash_end:]

app_path.write_text(s, encoding='utf-8')
print('UI v3 simplified')
# trigger fixed
