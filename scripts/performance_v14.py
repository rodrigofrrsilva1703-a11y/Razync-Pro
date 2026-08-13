from pathlib import Path

p = Path('database.py')
s = p.read_text(encoding='utf-8')

s = s.replace('engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}', 'engine_kwargs: dict[str, Any] = {"pool_pre_ping": False}', 1)
s = s.replace('_READ_CACHE_TTL = 30.0', '_READ_CACHE_TTL = 3600.0', 1)

# Cache count and paginated transaction reads too; writes already invalidate transaction-related caches below.
old_count = '''def count_transactions(user_id: int) -> int:\n    with engine.connect() as conn:\n        return int(conn.execute(select(func.count()).select_from(transactions).where(transactions.c.user_id == user_id)).scalar_one())\n'''
new_count = '''def count_transactions(user_id: int) -> int:\n    cached = _cache_get("tx_count", user_id)\n    if cached is not None:\n        return int(cached)\n    with engine.connect() as conn:\n        value = int(conn.execute(select(func.count()).select_from(transactions).where(transactions.c.user_id == user_id)).scalar_one())\n    return int(_cache_set("tx_count", user_id, value))\n'''
if old_count in s:
    s = s.replace(old_count, new_count, 1)

old_page = '''def list_transactions_page(user_id: int, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:\n    stmt = select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc()).limit(int(limit)).offset(int(offset))\n    with engine.connect() as conn:\n        rows = conn.execute(stmt).mappings().all()\n    return [dict(r) for r in rows]\n'''
new_page = '''def list_transactions_page(user_id: int, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:\n    cache_id = int(user_id) * 1000000 + int(offset) * 1000 + int(limit)\n    cached = _cache_get("tx_page", cache_id)\n    if cached is not None:\n        return cached\n    stmt = select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.tx_date.desc(), transactions.c.id.desc()).limit(int(limit)).offset(int(offset))\n    with engine.connect() as conn:\n        rows = conn.execute(stmt).mappings().all()\n    return _cache_set("tx_page", cache_id, [dict(r) for r in rows])\n'''
if old_page in s:
    s = s.replace(old_page, new_page, 1)

# Expand transaction invalidation so pagination/count never goes stale after a write.
needle = '_cache_invalidate("transactions", user_id)\n    for _k in [k for k in list(_READ_CACHE) if k[0] == "dashboard"]: _READ_CACHE.pop(_k, None)\n    _cache_invalidate("tx_docs", user_id)'
replacement = '_cache_invalidate("transactions", user_id)\n    _cache_invalidate("tx_count", user_id)\n    for _k in [k for k in list(_READ_CACHE) if k[0] in {"dashboard", "tx_page"}]: _READ_CACHE.pop(_k, None)\n    _cache_invalidate("tx_docs", user_id)'
s = s.replace(needle, replacement)

p.write_text(s, encoding='utf-8')
print('Performance V14 aplicada: sem pre-ping e cache persistente por processo')
