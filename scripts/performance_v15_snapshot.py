from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

marker = 'obligations = list(_snapshot.get("obligations") or [])\n\n# Dashboard metrics are calculated from the local snapshot — zero network calls while navigating.\n'
fix = '''obligations = list(_snapshot.get("obligations") or [])

# Shared financial context used by Dashboard and fiscal/management pages.
opening = opening_date_from(profile)
limit = annual_limit_for(opening, CURRENT_YEAR, profile.get("annual_limit"))
year_tx = transactions[(transactions["tx_date"].dt.year == CURRENT_YEAR)] if not transactions.empty else transactions
year_revenue = float(year_tx[year_tx["tx_type"] == "Receita"]["value"].sum()) if not year_tx.empty else 0.0
year_expense = float(year_tx[year_tx["tx_type"] == "Despesa"]["value"].sum()) if not year_tx.empty else 0.0
limit_pct = (year_revenue / limit * 100.0) if limit else 0.0

# Pagination context for the transaction history. Keep it local to the in-memory snapshot.
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
elif 'year_revenue = float(year_tx' not in s:
    raise SystemExit("Ponto de correção não encontrado em app.py")

p.write_text(s, encoding="utf-8")
print("Correção de contexto financeiro/paginação aplicada.")
