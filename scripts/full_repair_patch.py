from pathlib import Path

p = Path('database.py')
s = p.read_text(encoding='utf-8')

old = '''def load_user_snapshot(user_id: int) -> dict[str, Any]:\n    try:\n        with engine.connect() as conn:\n'''
new = '''def load_user_snapshot(user_id: int) -> dict[str, Any]:\n    if str(DATABASE_URL).startswith("sqlite"):\n        return {\n            "profile": get_profile(user_id),\n            "transactions": list_transactions(user_id),\n            "invoices": list_invoices(user_id),\n            "das": list_das(user_id),\n            "documents": list_documents(user_id),\n            "contacts": list_contacts(user_id),\n            "employees": list_employees(user_id),\n            "obligations": list_obligations(user_id),\n        }\n    try:\n        with engine.connect() as conn:\n'''
if old not in s:
    raise SystemExit('snapshot block not found')
s = s.replace(old, new, 1)

old2 = '''    _RECURRING_MATERIALIZE_CHECK[uid] = today\n    return generated\n'''
new2 = '''    if generated < max_occurrences:\n        _RECURRING_MATERIALIZE_CHECK[uid] = today\n    else:\n        _RECURRING_MATERIALIZE_CHECK.pop(uid, None)\n    return generated\n'''
if old2 not in s:
    raise SystemExit('recurring cap block not found')
s = s.replace(old2, new2, 1)

p.write_text(s, encoding='utf-8')
print('Functional repair patch applied')
