from pathlib import Path

p = Path('database.py')
s = p.read_text(encoding='utf-8')

marker = '_READ_CACHE_TTL = 30.0\n'
insert = '_READ_CACHE_TTL = 30.0\n_RECURRING_MATERIALIZE_CHECK: dict[int, date] = {}\n'
if '_RECURRING_MATERIALIZE_CHECK' not in s:
    if marker not in s:
        raise SystemExit('cache marker not found')
    s = s.replace(marker, insert, 1)

for old, new in [
    ('    _cache_invalidate("recurring_transactions", user_id)\n\n\ndef list_recurring_transactions', '    _cache_invalidate("recurring_transactions", user_id)\n    _RECURRING_MATERIALIZE_CHECK.pop(int(user_id), None)\n\n\ndef list_recurring_transactions'),
    ('    _cache_invalidate("recurring_transactions", user_id)\n    return bool(result.rowcount)\n\n\ndef delete_recurring_transaction', '    _cache_invalidate("recurring_transactions", user_id)\n    _RECURRING_MATERIALIZE_CHECK.pop(int(user_id), None)\n    return bool(result.rowcount)\n\n\ndef delete_recurring_transaction'),
    ('    _cache_invalidate("recurring_transactions", user_id)\n\n\ndef materialize_due_recurring', '    _cache_invalidate("recurring_transactions", user_id)\n    _RECURRING_MATERIALIZE_CHECK.pop(int(user_id), None)\n\n\ndef materialize_due_recurring'),
]:
    if new not in s:
        if old not in s:
            raise SystemExit(f'expected recurring block not found: {old[:60]}')
        s = s.replace(old, new, 1)

old_start = '''    today = today or date.today()\n    generated = 0\n    with engine.begin() as conn:\n'''
new_start = '''    today = today or date.today()\n    uid = int(user_id)\n    if _RECURRING_MATERIALIZE_CHECK.get(uid) == today:\n        return 0\n    generated = 0\n    with engine.begin() as conn:\n'''
if new_start not in s:
    if old_start not in s:
        raise SystemExit('materialize start not found')
    s = s.replace(old_start, new_start, 1)

old_end = '''    if generated:\n        _cache_invalidate("transactions", user_id)\n        _cache_invalidate("tx_docs", user_id)\n        for key in [key for key in list(_READ_CACHE) if key[0] == "dashboard"]:\n            _READ_CACHE.pop(key, None)\n    return generated\n'''
new_end = '''    if generated:\n        _cache_invalidate("transactions", user_id)\n        _cache_invalidate("tx_docs", user_id)\n        for key in [key for key in list(_READ_CACHE) if key[0] == "dashboard"]:\n            _READ_CACHE.pop(key, None)\n    _RECURRING_MATERIALIZE_CHECK[uid] = today\n    return generated\n'''
if new_end not in s:
    if old_end not in s:
        raise SystemExit('materialize end not found')
    s = s.replace(old_end, new_end, 1)

p.write_text(s, encoding='utf-8')
print('Performance V16 aplicada: recorrencias consultam o banco no maximo uma vez por usuario/dia, salvo alteracao da agenda.')
