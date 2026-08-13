from pathlib import Path

p = Path('database.py')
s = p.read_text(encoding='utf-8')

# Imports for safe in-process read cache
if 'import time\n' not in s:
    s = s.replace('import tempfile\n', 'import tempfile\nimport time\nimport copy\n', 1)

# Conservative reusable pool for Supabase Session Pooler
old = 'engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}\nif str(DATABASE_URL).startswith("sqlite"):\n    engine_kwargs["connect_args"] = {"check_same_thread": False}\nelse:\n    engine_kwargs["connect_args"] = {"connect_timeout": 10}\n    engine_kwargs["pool_recycle"] = 300\n'
new = '''engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}\nif str(DATABASE_URL).startswith("sqlite"):\n    engine_kwargs["connect_args"] = {"check_same_thread": False}\nelse:\n    engine_kwargs["connect_args"] = {"connect_timeout": 8}\n    engine_kwargs.update({\n        "pool_size": 3,\n        "max_overflow": 2,\n        "pool_recycle": 240,\n        "pool_timeout": 10,\n        "pool_use_lifo": True,\n    })\n'''
if old in s:
    s = s.replace(old, new, 1)

# Read-through cache: long enough to hide network RTT, immediately invalidated on writes.
marker = '\n\n@lru_cache(maxsize=1)\ndef init_db() -> None:'
if '_READ_CACHE:' not in s and marker in s:
    helpers = '''\n\n_READ_CACHE: dict[tuple[str, int], tuple[float, Any]] = {}\n_READ_CACHE_TTL = 30.0\n\ndef _cache_get(domain: str, user_id: int):\n    key = (domain, int(user_id))\n    item = _READ_CACHE.get(key)\n    if not item:\n        return None\n    created, value = item\n    if time.monotonic() - created > _READ_CACHE_TTL:\n        _READ_CACHE.pop(key, None)\n        return None\n    return copy.deepcopy(value)\n\ndef _cache_set(domain: str, user_id: int, value):\n    _READ_CACHE[(domain, int(user_id))] = (time.monotonic(), copy.deepcopy(value))\n    return copy.deepcopy(value)\n\ndef _cache_invalidate(domain: str, user_id: int) -> None:\n    _READ_CACHE.pop((domain, int(user_id)), None)\n\n'''
    s = s.replace(marker, helpers + marker, 1)
elif '_READ_CACHE_TTL = 8.0' in s:
    s = s.replace('_READ_CACHE_TTL = 8.0', '_READ_CACHE_TTL = 30.0', 1)

# Cache common read functions.
replacements = {
'''def get_profile(user_id: int) -> dict[str, Any]:\n    with engine.connect() as conn:\n        row = conn.execute(select(users.c.name, users.c.email, profiles).join(profiles, profiles.c.user_id == users.c.id).where(users.c.id == user_id)).mappings().first()\n    return dict(row) if row else {}''':
'''def get_profile(user_id: int) -> dict[str, Any]:\n    cached = _cache_get("profile", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        row = conn.execute(select(users.c.name, users.c.email, profiles).join(profiles, profiles.c.user_id == users.c.id).where(users.c.id == user_id)).mappings().first()\n    return _cache_set("profile", user_id, dict(row) if row else {})''',
'''def list_transactions(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_transactions(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("transactions", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc())).mappings().all()\n    return _cache_set("transactions", user_id, [dict(r) for r in rows])''',
'''def list_das(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(das_items).where(das_items.c.user_id == user_id).order_by(das_items.c.competence.desc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_das(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("das", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(das_items).where(das_items.c.user_id == user_id).order_by(das_items.c.competence.desc())).mappings().all()\n    return _cache_set("das", user_id, [dict(r) for r in rows])''',
'''def list_documents(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(documents.c.id, documents.c.filename, documents.c.mime_type, documents.c.category, documents.c.reference_month, documents.c.created_at).where(documents.c.user_id == user_id).order_by(documents.c.id.desc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_documents(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("documents", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(documents.c.id, documents.c.filename, documents.c.mime_type, documents.c.category, documents.c.reference_month, documents.c.created_at).where(documents.c.user_id == user_id).order_by(documents.c.id.desc())).mappings().all()\n    return _cache_set("documents", user_id, [dict(r) for r in rows])''',
'''def list_invoices(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(invoices).where(invoices.c.user_id == user_id).order_by(invoices.c.issue_date.desc(), invoices.c.id.desc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_invoices(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("invoices", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(invoices).where(invoices.c.user_id == user_id).order_by(invoices.c.issue_date.desc(), invoices.c.id.desc())).mappings().all()\n    return _cache_set("invoices", user_id, [dict(r) for r in rows])''',
'''def list_contacts(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(contacts).where(contacts.c.user_id == user_id).order_by(contacts.c.name.asc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_contacts(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("contacts", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(contacts).where(contacts.c.user_id == user_id).order_by(contacts.c.name.asc())).mappings().all()\n    return _cache_set("contacts", user_id, [dict(r) for r in rows])''',
'''def list_employees(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(employees).where(employees.c.user_id == user_id).order_by(employees.c.name.asc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_employees(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("employees", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(employees).where(employees.c.user_id == user_id).order_by(employees.c.name.asc())).mappings().all()\n    return _cache_set("employees", user_id, [dict(r) for r in rows])''',
'''def list_obligations(user_id: int) -> list[dict[str, Any]]:\n    with engine.connect() as conn:\n        rows = conn.execute(select(obligations).where(obligations.c.user_id == user_id).order_by(obligations.c.due_date.asc())).mappings().all()\n    return [dict(r) for r in rows]''':
'''def list_obligations(user_id: int) -> list[dict[str, Any]]:\n    cached = _cache_get("obligations", user_id)\n    if cached is not None:\n        return cached\n    with engine.connect() as conn:\n        rows = conn.execute(select(obligations).where(obligations.c.user_id == user_id).order_by(obligations.c.due_date.asc())).mappings().all()\n    return _cache_set("obligations", user_id, [dict(r) for r in rows])''',
}
for old_text, new_text in replacements.items():
    if old_text in s:
        s = s.replace(old_text, new_text, 1)

# Invalidate only the affected domain after successful mutations.
invalidations = [
    ('save_profile','profile'), ('add_transaction','transactions'), ('delete_transaction','transactions'),
    ('link_transaction_document','transactions'), ('upsert_das','das'), ('save_document','documents'),
    ('delete_document','documents'), ('add_invoice','invoices'), ('delete_invoice','invoices'),
    ('add_contact','contacts'), ('delete_contact','contacts'), ('add_employee','employees'),
    ('delete_employee','employees'), ('add_obligation','obligations'),
    ('update_obligation_status','obligations'), ('delete_obligation','obligations'),
]
for fname, domain in invalidations:
    start = s.find(f'def {fname}(')
    if start == -1:
        continue
    nxt = s.find('\n\ndef ', start + 5)
    if nxt == -1:
        nxt = len(s)
    block = s[start:nxt]
    if f'_cache_invalidate("{domain}", user_id)' in block:
        continue
    lines = block.rstrip().splitlines()
    lines.append(f'    _cache_invalidate("{domain}", user_id)')
    s = s[:start] + '\n'.join(lines) + '\n' + s[nxt:]

p.write_text(s, encoding='utf-8')
print('Performance V12 aplicada')
