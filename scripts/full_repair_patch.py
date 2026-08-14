from pathlib import Path

p = Path('database.py')
s = p.read_text(encoding='utf-8')

old = '''def load_user_snapshot(user_id: int) -> dict[str, Any]:\n    try:\n        with engine.connect() as conn:\n'''
new = '''def load_user_snapshot(user_id: int) -> dict[str, Any]:\n    if str(DATABASE_URL).startswith("sqlite"):\n        return {\n            "profile": get_profile(user_id),\n            "transactions": list_transactions(user_id),\n            "invoices": list_invoices(user_id),\n            "das": list_das(user_id),\n            "documents": list_documents(user_id),\n            "contacts": list_contacts(user_id),\n            "employees": list_employees(user_id),\n            "obligations": list_obligations(user_id),\n        }\n    try:\n        with engine.connect() as conn:\n'''
if old in s:
    s = s.replace(old, new, 1)
elif 'if str(DATABASE_URL).startswith("sqlite")' not in s:
    raise SystemExit('snapshot block not found')

old2 = '''    _RECURRING_MATERIALIZE_CHECK[uid] = today\n    return generated\n'''
new2 = '''    if generated < max_occurrences:\n        _RECURRING_MATERIALIZE_CHECK[uid] = today\n    else:\n        _RECURRING_MATERIALIZE_CHECK.pop(uid, None)\n    return generated\n'''
if old2 in s:
    s = s.replace(old2, new2, 1)
elif 'if generated < max_occurrences:' not in s:
    raise SystemExit('recurring cap block not found')

p.write_text(s, encoding='utf-8')

bp = Path('business_tools.py')
bs = bp.read_text(encoding='utf-8')
old3 = '''        "expenses": expenses,\n        "result": result,\n'''
new3 = '''        "expense": expenses,\n        "result": result,\n'''
if old3 in bs:
    bs = bs.replace(old3, new3, 1)
elif '"expense": expenses' not in bs:
    raise SystemExit('financial analysis contract block not found')
bp.write_text(bs, encoding='utf-8')

print('Functional repair patch applied')
