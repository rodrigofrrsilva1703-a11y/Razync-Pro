from pathlib import Path

# database.py: initialize schema once per Streamlit process
p = Path('database.py')
s = p.read_text(encoding='utf-8')
if 'from functools import lru_cache' not in s:
    s = s.replace('import tempfile\n', 'import tempfile\nfrom functools import lru_cache\n', 1)
s = s.replace('def init_db() -> None:\n    try:', '@lru_cache(maxsize=1)\ndef init_db() -> None:\n    try:', 1)
p.write_text(s, encoding='utf-8')

# app.py: reuse dev auth and fetch only datasets required by the current page
p = Path('app.py')
s = p.read_text(encoding='utf-8')
old_login = '''def ensure_login() -> dict:\n    email = "dev@local"\n    password = "dev"\n    user = authenticate(email, password)\n    if not user:\n        create_user("Desenvolvimento", email, password)\n        user = authenticate(email, password)\n    if not user:\n        st.stop()\n    st.session_state.user = user\n    return user\n'''
new_login = '''def ensure_login() -> dict:\n    cached = st.session_state.get("user")\n    if cached and cached.get("id"):\n        return cached\n    email = "dev@local"\n    password = "dev"\n    user = authenticate(email, password)\n    if not user:\n        create_user("Desenvolvimento", email, password)\n        user = authenticate(email, password)\n    if not user:\n        st.stop()\n    st.session_state.user = user\n    return user\n'''
s = s.replace(old_login, new_login, 1)
old_data = '''user = ensure_login()\nuid = int(user["id"])\nprofile = get_profile(uid)\ntransactions = tx_df(uid)\ninvoices = invoice_df(uid)\ndas_rows = list_das(uid)\ndocs = list_documents(uid)\nemployees = list_employees(uid)\ncontacts = list_contacts(uid)\nobligations = list_obligations(uid)\n\npending_page = st.session_state.pop("_navigate_to", None)\nif pending_page:\n    st.session_state["_current_page"] = pending_page\n\npage = st.session_state.get("_current_page", "Dashboard")\nall_pages = [p for pages in NAV_GROUPS.values() for p in pages]\nif page not in all_pages:\n    page = "Dashboard"\n    st.session_state["_current_page"] = page\n'''
new_data = '''user = ensure_login()\nuid = int(user["id"])\n\npending_page = st.session_state.pop("_navigate_to", None)\nif pending_page:\n    st.session_state["_current_page"] = pending_page\n\npage = st.session_state.get("_current_page", "Dashboard")\nall_pages = [p for pages in NAV_GROUPS.values() for p in pages]\nif page not in all_pages:\n    page = "Dashboard"\n    st.session_state["_current_page"] = page\n\nprofile = get_profile(uid)\ntransactions = pd.DataFrame(columns=["id","tx_date","tx_type","description","category","value","document_number","counterparty","payment_method"])\ninvoices = pd.DataFrame()\ndas_rows = []\ndocs = []\nemployees = []\ncontacts = []\nobligations = []\n\ntx_pages = {"Dashboard","Movimentações","Importar Extrato","Conciliação","Fluxo de Caixa","Análise Financeira","Central Fiscal","Fechamento Mensal","Relatório Mensal","Notas Fiscais","DASN-SIMEI","Central de Relatórios","Assistente Razync","Backup","Primeiros Passos"}\ninvoice_pages = {"Dashboard","Conciliação","Central Fiscal","Fechamento Mensal","Notas Fiscais","Central de Relatórios","Assistente Razync","Backup"}\ndas_pages = {"Dashboard","Central Fiscal","Fechamento Mensal","DAS","DASN-SIMEI","Central de Relatórios","Assistente Razync","Backup","Primeiros Passos"}\ndoc_pages = {"Dashboard","Fechamento Mensal","Documentos","Central de Relatórios","Backup","Primeiros Passos"}\nemployee_pages = {"Empregado","DASN-SIMEI","Backup"}\ncontact_pages = {"Movimentações","Notas Fiscais","Clientes e Fornecedores","Backup"}\nobligation_pages = {"Dashboard","Central Fiscal","Fechamento Mensal","Obrigações","Central de Relatórios","Backup"}\n\nif page in tx_pages:\n    transactions = tx_df(uid)\nif page in invoice_pages:\n    invoices = invoice_df(uid)\nif page in das_pages:\n    das_rows = list_das(uid)\nif page in doc_pages:\n    docs = list_documents(uid)\nif page in employee_pages:\n    employees = list_employees(uid)\nif page in contact_pages:\n    contacts = list_contacts(uid)\nif page in obligation_pages:\n    obligations = list_obligations(uid)\n'''
if old_data not in s:
    raise SystemExit('data loading block not found')
s = s.replace(old_data, new_data, 1)
p.write_text(s, encoding='utf-8')
print('performance v10 applied')
# trigger v10
