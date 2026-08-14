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
closing_marker = '''def monthly_closing(transactions: pd.DataFrame, invoices: pd.DataFrame, documents: list[dict], das_rows: list[dict], year: int, month: int) -> dict:\n'''
financial_marker = '''def financial_analysis(transactions: pd.DataFrame, year: int) -> dict:\n'''
closing_pos = bs.find(closing_marker)
financial_pos = bs.find(financial_marker)
if closing_pos < 0 or financial_pos < 0:
    raise SystemExit('business tool functions not found')
closing_head = bs[:closing_pos]
closing_body = bs[closing_pos:financial_pos]
financial_body = bs[financial_pos:]
closing_old = '''        "expenses": expenses,\n        "result": result,\n'''
closing_new = '''        "expense": expenses,\n        "expenses": expenses,\n        "result": result,\n'''
if closing_old in closing_body:
    closing_body = closing_body.replace(closing_old, closing_new, 1)
elif '"expense": expenses' not in closing_body:
    raise SystemExit('monthly closing return block not found')
financial_old = '''        "expenses": expenses,\n        "result": result,\n'''
financial_new = '''        "expense": expenses,\n        "expenses": expenses,\n        "result": result,\n'''
if financial_old in financial_body:
    financial_body = financial_body.replace(financial_old, financial_new, 1)
elif '"expense": expenses' not in financial_body:
    raise SystemExit('financial analysis return block not found')
bp.write_text(closing_head + closing_body + financial_body, encoding='utf-8')

ap = Path('app.py')
a = ap.read_text(encoding='utf-8')
a = a.replace(
    'financial_summary_pdf(profile, analysis_year, analysis, checks)',
    'financial_summary_pdf(profile, analysis_year, analysis)',
)
a = a.replace(
    'monthly_report_pdf(profile,month,year,r["with_doc"],r["without_doc"],r["services"],r["sales"])',
    'monthly_report_pdf(profile, year, [r])',
)
if 'financial_summary_pdf(profile, analysis_year, analysis, checks)' in a:
    raise SystemExit('financial PDF call was not repaired')
if 'monthly_report_pdf(profile,month,year,r["with_doc"]' in a:
    raise SystemExit('monthly PDF call was not repaired')
ap.write_text(a, encoding='utf-8')

print('Functional repair patch applied')
