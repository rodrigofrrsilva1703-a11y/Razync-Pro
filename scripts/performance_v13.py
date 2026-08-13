from pathlib import Path

# --- database.py ---
p = Path('database.py')
s = p.read_text(encoding='utf-8')
if ' func,' not in s and 'func,' not in s:
    s = s.replace('MetaData, String, Table, Text, create_engine, delete, insert, select, update\n)', 'MetaData, String, Table, Text, create_engine, delete, insert, select, update, func, case, extract\n)', 1)

anchor = '\n\ndef delete_transaction(user_id: int, item_id: int) -> None:'
if 'def dashboard_financial_summary(' not in s and anchor in s:
    funcs = '''\n\ndef dashboard_financial_summary(user_id: int, year: int, month: int) -> dict[str, Any]:\n    cache_key = int(user_id) * 100000 + int(year) * 100 + int(month)\n    cached = _cache_get("dashboard", cache_key)\n    if cached is not None:\n        return cached\n    year_cond = extract("year", transactions.c.tx_date) == int(year)\n    month_cond = extract("month", transactions.c.tx_date) == int(month)\n    stmt = select(\n        func.count(transactions.c.id).label("transaction_count"),\n        func.coalesce(func.sum(case((year_cond & (transactions.c.tx_type == "Receita"), transactions.c.value), else_=0)), 0).label("year_revenue"),\n        func.coalesce(func.sum(case((year_cond & (transactions.c.tx_type == "Despesa"), transactions.c.value), else_=0)), 0).label("year_expense"),\n        func.coalesce(func.sum(case((year_cond & month_cond & (transactions.c.tx_type == "Receita"), transactions.c.value), else_=0)), 0).label("month_in"),\n        func.coalesce(func.sum(case((year_cond & month_cond & (transactions.c.tx_type == "Despesa"), transactions.c.value), else_=0)), 0).label("month_out"),\n    ).where(transactions.c.user_id == user_id)\n    with engine.connect() as conn:\n        row = conn.execute(stmt).mappings().one()\n    result = {k: float(v or 0) if k != "transaction_count" else int(v or 0) for k, v in dict(row).items()}\n    return _cache_set("dashboard", cache_key, result)\n\ndef transaction_document_numbers(user_id: int) -> list[str]:\n    cached = _cache_get("tx_docs", user_id)\n    if cached is not None:\n        return cached\n    stmt = select(transactions.c.document_number).where(\n        transactions.c.user_id == user_id,\n        transactions.c.document_number.is_not(None),\n        transactions.c.document_number != ""\n    )\n    with engine.connect() as conn:\n        rows = conn.execute(stmt).scalars().all()\n    return _cache_set("tx_docs", user_id, [str(x) for x in rows])\n\ndef count_transactions(user_id: int) -> int:\n    with engine.connect() as conn:\n        return int(conn.execute(select(func.count()).select_from(transactions).where(transactions.c.user_id == user_id)).scalar_one())\n\ndef list_transactions_page(user_id: int, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:\n    stmt = select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc()).limit(int(limit)).offset(int(offset))\n    with engine.connect() as conn:\n        rows = conn.execute(stmt).mappings().all()\n    return [dict(r) for r in rows]\n'''
    s = s.replace(anchor, funcs + anchor, 1)

# transaction mutations also invalidate dashboard/doc-number caches
for fname in ['add_transaction','delete_transaction','link_transaction_document']:
    start=s.find(f'def {fname}(')
    if start!=-1:
        nxt=s.find('\n\ndef ',start+5)
        if nxt==-1:nxt=len(s)
        block=s[start:nxt]
        additions=[]
        if '_cache_invalidate("dashboard"' not in block:
            # dashboard cache uses composite keys, so clear all dashboard entries conservatively
            additions.append('    for _k in [k for k in list(_READ_CACHE) if k[0] == "dashboard"]: _READ_CACHE.pop(_k, None)')
        if '_cache_invalidate("tx_docs", user_id)' not in block:
            additions.append('    _cache_invalidate("tx_docs", user_id)')
        if additions:
            lines=block.rstrip().splitlines()+additions
            s=s[:start]+'\n'.join(lines)+'\n'+s[nxt:]
p.write_text(s,encoding='utf-8')

# --- app.py ---
p=Path('app.py')
a=p.read_text(encoding='utf-8')
a=a.replace('update_obligation_status, upsert_das, link_transaction_document,', 'update_obligation_status, upsert_das, link_transaction_document,\n    dashboard_financial_summary, transaction_document_numbers, count_transactions, list_transactions_page,',1)
a=a.replace('tx_pages = {"Dashboard","Movimentações",', 'tx_pages = {"Importar Extrato",',1)
# dashboard-specific lightweight transaction context
needle='''if page in obligation_pages:\n    obligations = list_obligations(uid)\n\nwith st.sidebar:'''
replacement='''if page in obligation_pages:\n    obligations = list_obligations(uid)\n\n_dashboard_stats = None\nif page == "Dashboard":\n    _dashboard_stats = dashboard_financial_summary(uid, CURRENT_YEAR, date.today().month)\n    _docs = transaction_document_numbers(uid)\n    transactions = pd.DataFrame({"document_number": _docs}) if _docs else pd.DataFrame(columns=["document_number"])\nif page == "Movimentações":\n    page_size = 50\n    current_tx_page = int(st.session_state.get("tx_history_page", 1))\n    total_tx = count_transactions(uid)\n    max_tx_page = max(1, (total_tx + page_size - 1) // page_size)\n    current_tx_page = min(max(current_tx_page, 1), max_tx_page)\n    rows = list_transactions_page(uid, page_size, (current_tx_page - 1) * page_size)\n    transactions = pd.DataFrame(rows)\n    if transactions.empty:\n        transactions = pd.DataFrame(columns=["id","tx_date","tx_type","description","category","value","document_number","counterparty","payment_method"])\n    else:\n        transactions["tx_date"] = pd.to_datetime(transactions["tx_date"])\n\nwith st.sidebar:'''
if needle in a:
    a=a.replace(needle,replacement,1)
# global year totals: dashboard uses aggregate
old='''year_tx = transactions[(transactions["tx_date"].dt.year==CURRENT_YEAR)] if not transactions.empty else transactions\nyear_revenue = float(year_tx[year_tx["tx_type"]=="Receita"]["value"].sum()) if not year_tx.empty else 0.0\nyear_expense = float(year_tx[year_tx["tx_type"]=="Despesa"]["value"].sum()) if not year_tx.empty else 0.0'''
new='''if page == "Dashboard" and _dashboard_stats is not None:\n    year_revenue = float(_dashboard_stats["year_revenue"])\n    year_expense = float(_dashboard_stats["year_expense"])\n    year_tx = pd.DataFrame()\nelse:\n    year_tx = transactions[(transactions["tx_date"].dt.year==CURRENT_YEAR)] if not transactions.empty and "tx_date" in transactions.columns else transactions\n    year_revenue = float(year_tx[year_tx["tx_type"]=="Receita"]["value"].sum()) if not year_tx.empty else 0.0\n    year_expense = float(year_tx[year_tx["tx_type"]=="Despesa"]["value"].sum()) if not year_tx.empty else 0.0'''
if old in a:a=a.replace(old,new,1)
# dashboard month calculation from aggregate and onboarding count
old2='''    onboarding = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))'''
new2='''    onboarding = onboarding_progress(profile, bool(_dashboard_stats and _dashboard_stats["transaction_count"]), bool(das_rows), bool(docs))'''
a=a.replace(old2,new2,1)
old3='''    today = date.today()\n    month_tx = transactions[(transactions["tx_date"].dt.year == CURRENT_YEAR) & (transactions["tx_date"].dt.month == today.month)] if not transactions.empty else transactions\n    month_in = float(month_tx[month_tx["tx_type"] == "Receita"]["value"].sum()) if not month_tx.empty else 0.0\n    month_out = float(month_tx[month_tx["tx_type"] == "Despesa"]["value"].sum()) if not month_tx.empty else 0.0\n    month_result = month_in - month_out'''
new3='''    today = date.today()\n    month_in = float(_dashboard_stats["month_in"] if _dashboard_stats else 0)\n    month_out = float(_dashboard_stats["month_out"] if _dashboard_stats else 0)\n    month_result = month_in - month_out'''
if old3 in a:a=a.replace(old3,new3,1)
# action_items should know whether transactions exist even without downloading them
old4='''    priorities = action_items(profile, transactions, invoices, das_rows, obligations, limit, year_revenue)'''
new4='''    _action_tx = transactions\n    if _dashboard_stats and _dashboard_stats["transaction_count"] and _action_tx.empty:\n        _action_tx = pd.DataFrame({"document_number":[""]})\n    priorities = action_items(profile, _action_tx, invoices, das_rows, obligations, limit, year_revenue)'''
a=a.replace(old4,new4,1)
# add pagination controls under Movimentações history
needle2='''        st.dataframe(view[["id","Data","Tipo","Descrição","Categoria","Valor"]], use_container_width=True, hide_index=True, column_config={"id":None,"Valor":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"Data":st.column_config.DateColumn("Data",format="DD/MM/YYYY")})\n        with st.expander("Excluir um lançamento"):'''
repl2='''        st.dataframe(view[["id","Data","Tipo","Descrição","Categoria","Valor"]], use_container_width=True, hide_index=True, column_config={"id":None,"Valor":st.column_config.NumberColumn("Valor",format="R$ %.2f"),"Data":st.column_config.DateColumn("Data",format="DD/MM/YYYY")})\n        if total_tx > page_size:\n            pprev, pinfo, pnext = st.columns([1,2,1])\n            if pprev.button("← Anterior", disabled=current_tx_page <= 1, use_container_width=True):\n                st.session_state["tx_history_page"] = current_tx_page - 1; st.rerun()\n            pinfo.caption(f"Página {current_tx_page} de {max_tx_page} • {total_tx} lançamentos")\n            if pnext.button("Próxima →", disabled=current_tx_page >= max_tx_page, use_container_width=True):\n                st.session_state["tx_history_page"] = current_tx_page + 1; st.rerun()\n        with st.expander("Excluir um lançamento"):'''
if needle2 in a:a=a.replace(needle2,repl2,1)
p.write_text(a,encoding='utf-8')
print('Performance V13 aplicada')
