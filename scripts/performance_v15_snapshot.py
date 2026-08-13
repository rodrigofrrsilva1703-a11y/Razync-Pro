from pathlib import Path

# ---------------- database.py ----------------
p = Path('database.py')
s = p.read_text(encoding='utf-8')

if 'import json\n' not in s:
    s = s.replace('import copy\n', 'import copy\nimport json\n', 1)

s = s.replace('from datetime import datetime\n', 'from datetime import datetime, date\n', 1)
s = s.replace('MetaData, String, Table, Text, create_engine, delete, insert, select, update, func, case, extract\n',
              'MetaData, String, Table, Text, create_engine, delete, insert, select, update, func, case, extract, text\n', 1)

# Remote DB: reuse connections without an extra SELECT 1 before every checkout.
s = s.replace('engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}',
              'engine_kwargs: dict[str, Any] = {"pool_pre_ping": False}', 1)
s = s.replace('"pool_recycle": 240,', '"pool_recycle": 1800,', 1)

# Session/process version counter. Any mutation invalidates the in-memory snapshot.
if '_USER_VERSION:' not in s:
    marker = '_READ_CACHE: dict[tuple[str, int], tuple[float, Any]] = {}\n'
    s = s.replace(marker, '_USER_VERSION: dict[int, int] = {}\n' + marker, 1)

old_inv = '''def _cache_invalidate(domain: str, user_id: int) -> None:\n    _READ_CACHE.pop((domain, int(user_id)), None)'''
new_inv = '''def _cache_invalidate(domain: str, user_id: int) -> None:\n    uid = int(user_id)\n    _READ_CACHE.pop((domain, uid), None)\n    _USER_VERSION[uid] = _USER_VERSION.get(uid, 0) + 1\n\ndef data_version(user_id: int) -> int:\n    return _USER_VERSION.get(int(user_id), 0)'''
if old_inv in s:
    s = s.replace(old_inv, new_inv, 1)

# PostgreSQL schema is managed by Supabase migrations. Avoid create_all/introspection on every cold process.
old_init = '''@lru_cache(maxsize=1)\ndef init_db() -> None:\n    try:\n        metadata.create_all(engine)\n    except OperationalError as exc:\n        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None'''
new_init = '''@lru_cache(maxsize=1)\ndef init_db() -> None:\n    if not str(DATABASE_URL).startswith("sqlite"):\n        return\n    try:\n        metadata.create_all(engine)\n    except OperationalError as exc:\n        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None'''
if old_init in s:
    s = s.replace(old_init, new_init, 1)

# One round-trip loads the complete MEI working set (document binary content remains lazy).
if 'def load_user_snapshot(' not in s:
    marker = '\n\ndef _hash_password(password: str, salt: bytes | None = None) -> str:'
    snapshot_fn = r'''

def _snapshot_date(value):
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return value
    return value


def load_user_snapshot(user_id: int) -> dict[str, Any]:
    try:
        with engine.connect() as conn:
            raw = conn.execute(
                text("select public.razync_user_snapshot(:uid)"),
                {"uid": int(user_id)},
            ).scalar_one()
    except OperationalError as exc:
        raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None

    if isinstance(raw, str):
        raw = json.loads(raw)
    snapshot = dict(raw or {})
    snapshot.setdefault("profile", {})
    for key in ("transactions", "invoices", "das", "documents", "contacts", "employees", "obligations"):
        snapshot.setdefault(key, [])

    profile = snapshot.get("profile") or {}
    if profile.get("opening_date"):
        profile["opening_date"] = _snapshot_date(profile.get("opening_date"))
    snapshot["profile"] = profile

    for row in snapshot["transactions"]:
        row["tx_date"] = _snapshot_date(row.get("tx_date"))
    for row in snapshot["invoices"]:
        row["issue_date"] = _snapshot_date(row.get("issue_date"))
    for row in snapshot["das"]:
        row["due_date"] = _snapshot_date(row.get("due_date"))
        row["payment_date"] = _snapshot_date(row.get("payment_date"))
    for row in snapshot["employees"]:
        row["admission_date"] = _snapshot_date(row.get("admission_date"))
    for row in snapshot["obligations"]:
        row["due_date"] = _snapshot_date(row.get("due_date"))
    return snapshot
'''
    s = s.replace(marker, snapshot_fn + marker, 1)

p.write_text(s, encoding='utf-8')

# ---------------- app.py ----------------
p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Add snapshot imports.
s = s.replace('dashboard_financial_summary, transaction_document_numbers, count_transactions, list_transactions_page,\n    DatabaseConnectionError,',
              'dashboard_financial_summary, transaction_document_numbers, count_transactions, list_transactions_page,\n    load_user_snapshot, data_version, DatabaseConnectionError,', 1)

# Do not authenticate against Supabase on every Streamlit rerun.
old_login = '''def ensure_login() -> dict:\n    email = "dev@local"\n    password = "dev"\n    user = authenticate(email, password)\n    if not user:\n        create_user("Desenvolvimento", email, password)\n        user = authenticate(email, password)\n    if not user:\n        st.stop()\n    st.session_state.user = user\n    return user'''
new_login = '''def ensure_login() -> dict:\n    existing = st.session_state.get("user")\n    if isinstance(existing, dict) and existing.get("id"):\n        return existing\n    email = "dev@local"\n    password = "dev"\n    user = authenticate(email, password)\n    if not user:\n        create_user("Desenvolvimento", email, password)\n        user = authenticate(email, password)\n    if not user:\n        st.stop()\n    st.session_state.user = user\n    return user'''
if old_login in s:
    s = s.replace(old_login, new_login, 1)

# Replace page-by-page remote reads with one session snapshot.
start = s.find('profile = get_profile(uid)\n')
end = s.find('\nwith st.sidebar:', start)
if start != -1 and end != -1:
    new_block = r'''# PERFORMANCE V15: one Supabase round-trip per session/data change.
_snapshot_key = f"_mei_snapshot_{uid}"
_snapshot_version_key = f"_mei_snapshot_version_{uid}"
_current_data_version = data_version(uid)
if _snapshot_key not in st.session_state or st.session_state.get(_snapshot_version_key) != _current_data_version:
    try:
        st.session_state[_snapshot_key] = load_user_snapshot(uid)
        st.session_state[_snapshot_version_key] = _current_data_version
    except DatabaseConnectionError as exc:
        st.error("Não foi possível sincronizar os dados do Razync Pro.")
        st.warning(str(exc))
        st.stop()

_snapshot = st.session_state[_snapshot_key]
profile = dict(_snapshot.get("profile") or {})

transactions = pd.DataFrame(_snapshot.get("transactions") or [])
if transactions.empty:
    transactions = pd.DataFrame(columns=["id","tx_date","tx_type","description","category","value","document_number","counterparty","payment_method"])
else:
    transactions["tx_date"] = pd.to_datetime(transactions["tx_date"])

invoices = pd.DataFrame(_snapshot.get("invoices") or [])
if not invoices.empty:
    invoices["issue_date"] = pd.to_datetime(invoices["issue_date"])

das_rows = list(_snapshot.get("das") or [])
docs = list(_snapshot.get("documents") or [])
employees = list(_snapshot.get("employees") or [])
contacts = list(_snapshot.get("contacts") or [])
obligations = list(_snapshot.get("obligations") or [])

# Dashboard metrics are calculated from the local snapshot — zero network calls while navigating.
_dashboard_stats = None
if page == "Dashboard":
    today = date.today()
    year_local = transactions[transactions["tx_date"].dt.year == CURRENT_YEAR] if not transactions.empty else transactions
    month_local = year_local[year_local["tx_date"].dt.month == today.month] if not year_local.empty else year_local
    _dashboard_stats = {
        "transaction_count": int(len(transactions)),
        "year_revenue": float(year_local.loc[year_local["tx_type"] == "Receita", "value"].sum()) if not year_local.empty else 0.0,
        "year_expense": float(year_local.loc[year_local["tx_type"] == "Despesa", "value"].sum()) if not year_local.empty else 0.0,
        "month_in": float(month_local.loc[month_local["tx_type"] == "Receita", "value"].sum()) if not month_local.empty else 0.0,
        "month_out": float(month_local.loc[month_local["tx_type"] == "Despesa", "value"].sum()) if not month_local.empty else 0.0,
    }

# Movimentações paginate the in-memory snapshot; changing pages does not touch Supabase.
if page == "Movimentações":
    page_size = 50
    total_tx = len(transactions)
    current_tx_page = int(st.session_state.get("tx_history_page", 1))
    max_tx_page = max(1, (total_tx + page_size - 1) // page_size)
    current_tx_page = min(max(current_tx_page, 1), max_tx_page)
    offset = (current_tx_page - 1) * page_size
    transactions = transactions.iloc[offset:offset + page_size].copy()
'''
    s = s[:start] + new_block + s[end:]

p.write_text(s, encoding='utf-8')
print('Performance V15 snapshot architecture applied')
