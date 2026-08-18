from pathlib import Path

app = Path('app.py')
s = app.read_text(encoding='utf-8')

anchor = 'from dashboard_workspace import render_dashboard_workspace\n'
if 'from sidebar_workspace import render_sidebar\n' not in s:
    s = s.replace(anchor, anchor + 'from sidebar_workspace import render_sidebar\n', 1)

nav_anchor = '''def navigate_to(destination: str) -> None:\n    st.session_state["_navigate_to"] = destination\n    st.rerun()\n\n\n'''
refresh_block = '''def refresh_snapshot() -> None:\n    st.session_state.pop(_snapshot_key, None)\n    st.session_state.pop(_snapshot_version_key, None)\n    st.toast("Dados atualizados com segurança.")\n    st.rerun()\n\n\n'''
if 'def refresh_snapshot() -> None:' not in s:
    s = s.replace(nav_anchor, nav_anchor + refresh_block, 1)

start = s.index('with st.sidebar:\n')
end = s.index('undo_transaction = st.session_state.get("_undo_transaction")', start)
replacement = '''render_sidebar(\n    profile=profile,\n    user=user,\n    transactions=transactions,\n    das_rows=das_rows,\n    documents=docs,\n    page=page,\n    brand_logo_data_uri=BRAND_LOGO_DATA_URI,\n    navigate=navigate_to,\n    refresh_data=refresh_snapshot,\n    logout=logout_current_user,\n)\n\n'''
s = s[:start] + replacement + s[end:]

app.write_text(s, encoding='utf-8')
print('Final polish applied')
