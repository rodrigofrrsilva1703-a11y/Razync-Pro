from pathlib import Path

app_path = Path('app.py')
text = app_path.read_text(encoding='utf-8')

import_line = 'from navigation_config import SIDEBAR_LABELS, SIDEBAR_GROUPS, SIDEBAR_SECONDARY_GROUPS, SIDEBAR_ICONS\n'
if import_line not in text:
    anchor = 'from customer_experience import (\n    OFFICIAL_SERVICES, build_today_plan, das_journey, financial_story,\n    integration_catalog, next_onboarding_step, security_checklist,\n    transaction_restore_payload,\n)\n'
    if anchor not in text:
        raise SystemExit('customer_experience import anchor not found')
    text = text.replace(anchor, anchor + import_line, 1)

start = text.find('sidebar_labels = {')
end_marker = '\nst.markdown(\n    """\n    <style>'
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('sidebar configuration block not found')
text = text[:start] + text[end:]

text = text.replace('sidebar_labels[', 'SIDEBAR_LABELS[')
text = text.replace('sidebar_icons[', 'SIDEBAR_ICONS[')
text = text.replace('sidebar_groups.items()', 'SIDEBAR_GROUPS.items()')

old_loop = '''        for group_title, destinations in SIDEBAR_GROUPS.items():\n            with st.expander(group_title, expanded=page in destinations):\n                for destination in destinations:\n                    if st.button(\n                        SIDEBAR_LABELS[destination],\n                        key=f"grouped_nav_{destination}",\n                        icon=SIDEBAR_ICONS[destination],\n                        disabled=page == destination,\n                        width="stretch",\n                    ):\n                        st.session_state["_navigate_to"] = destination\n                        st.rerun()\n\n        setup_progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))\n'''
new_loop = '''        for group_title, destinations in SIDEBAR_GROUPS.items():\n            with st.expander(group_title, expanded=page in destinations):\n                for destination in destinations:\n                    if st.button(\n                        SIDEBAR_LABELS[destination],\n                        key=f"grouped_nav_{destination}",\n                        icon=SIDEBAR_ICONS[destination],\n                        disabled=page == destination,\n                        width="stretch",\n                    ):\n                        st.session_state["_navigate_to"] = destination\n                        st.rerun()\n\n        secondary_pages = [item for pages in SIDEBAR_SECONDARY_GROUPS.values() for item in pages]\n        with st.expander("Mais ferramentas", expanded=page in secondary_pages):\n            for secondary_title, destinations in SIDEBAR_SECONDARY_GROUPS.items():\n                st.caption(secondary_title.upper())\n                for destination in destinations:\n                    if st.button(\n                        SIDEBAR_LABELS[destination],\n                        key=f"secondary_nav_{destination}",\n                        icon=SIDEBAR_ICONS[destination],\n                        disabled=page == destination,\n                        width="stretch",\n                    ):\n                        st.session_state["_navigate_to"] = destination\n                        st.rerun()\n\n        setup_progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))\n'''
if old_loop not in text:
    raise SystemExit('sidebar render loop not found')
text = text.replace(old_loop, new_loop, 1)

# Keep the NFS-e importer as an internal route opened from Notas Fiscais; do not duplicate it in the main sidebar.
if 'SIDEBAR_LABELS' not in text or 'SIDEBAR_SECONDARY_GROUPS' not in text:
    raise SystemExit('navigation import did not apply')

app_path.write_text(text, encoding='utf-8')
print('UX V2 navigation patch applied')
