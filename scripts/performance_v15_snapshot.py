from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

marker = 'obligations = list(_snapshot.get("obligations") or [])\n\n# Dashboard metrics are calculated from the local snapshot — zero network calls while navigating.\n'
fix = '''obligations = list(_snapshot.get("obligations") or [])

opening = opening_date_from(profile)
limit = annual_limit_for(opening, CURRENT_YEAR, profile.get("annual_limit"))
year_tx = transactions[(transactions["tx_date"].dt.year == CURRENT_YEAR)] if not transactions.empty else transactions
year_revenue = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
year_expense = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0
limit_pct = (year_revenue / limit * 100.0) if limit else 0.0

page_size = 50
total_tx = len(transactions)
current_tx_page = int(st.session_state.get("tx_history_page", 1))
max_tx_page = max(1, (total_tx + page_size - 1) // page_size)
current_tx_page = min(max(current_tx_page, 1), max_tx_page)
if page == "Movimentações" and not transactions.empty:
    offset = (current_tx_page - 1) * page_size
    transactions = transactions.iloc[offset:offset + page_size].copy()

# Dashboard metrics are calculated from the local snapshot — zero network calls while navigating.
'''
if marker in s:
    s = s.replace(marker, fix, 1)

anchor = '# Dashboard metrics are calculated from the local snapshot — zero network calls while navigating.\n_dashboard_stats = None\n'
sidebar = '''with st.sidebar:
    st.markdown("### RAZYNC PRO")
    st.caption("Contabilidade simples para MEI")
    st.selectbox("Tema", ["Claro", "Escuro"], key="ui_theme")
    st.markdown("**Navegação**")
    if page == "Dashboard":
        st.info("⌂ Início")
    elif st.button("⌂ Início", key="nav_home", use_container_width=True):
        st.session_state["_navigate_to"] = "Dashboard"
        st.rerun()
    groups = {
        "Financeiro": NAV_GROUPS["Financeiro"],
        "Fiscal MEI": NAV_GROUPS["Fiscal MEI"],
        "Gestão": NAV_GROUPS["Gestão"],
        "Relatórios": NAV_GROUPS["Relatórios"],
        "Configurações": NAV_GROUPS["Configurações"],
    }
    for group, pages in groups.items():
        with st.expander(group, expanded=(group_for_page(page) == group)):
            for nav_page in pages:
                if nav_page == page:
                    st.info(nav_page)
                elif st.button(nav_page, key=f"nav_{group}_{nav_page}", use_container_width=True):
                    st.session_state["_navigate_to"] = nav_page
                    st.rerun()

'''
if 'with st.sidebar:' not in s:
    if anchor not in s:
        raise SystemExit("anchor not found")
    s = s.replace(anchor, sidebar + anchor, 1)

p.write_text(s, encoding="utf-8")
print("Barra lateral restaurada")
