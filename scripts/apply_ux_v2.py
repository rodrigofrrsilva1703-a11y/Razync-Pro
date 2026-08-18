from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

import_anchor = '''from customer_experience import (
    OFFICIAL_SERVICES, build_today_plan, das_journey, financial_story,
    integration_catalog, next_onboarding_step, security_checklist,
    transaction_restore_payload,
)
'''
nav_import = 'from navigation_config import SIDEBAR_LABELS, SIDEBAR_GROUPS, SIDEBAR_SECONDARY_GROUPS, SIDEBAR_ICONS\n'
if nav_import not in text:
    if import_anchor not in text:
        raise RuntimeError("Import anchor not found")
    text = text.replace(import_anchor, import_anchor + nav_import, 1)

start = text.find("sidebar_labels = {")
style_marker = '\nst.markdown(\n    """\n    <style>'
end = text.find(style_marker, start)
if start == -1 or end == -1:
    raise RuntimeError("Sidebar configuration block not found")
text = text[:start] + text[end:]

text = text.replace('sidebar_labels[', 'SIDEBAR_LABELS[')
text = text.replace('sidebar_icons[', 'SIDEBAR_ICONS[')
text = text.replace('sidebar_groups.items()', 'SIDEBAR_GROUPS.items()')

needle = '''        for group_title, destinations in SIDEBAR_GROUPS.items():
            with st.expander(group_title, expanded=page in destinations):
                for destination in destinations:
                    if st.button(
                        SIDEBAR_LABELS[destination],
                        key=f"grouped_nav_{destination}",
                        icon=SIDEBAR_ICONS[destination],
                        disabled=page == destination,
                        width="stretch",
                    ):
                        st.session_state["_navigate_to"] = destination
                        st.rerun()

        setup_progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))
'''
replacement = '''        for group_title, destinations in SIDEBAR_GROUPS.items():
            with st.expander(group_title, expanded=page in destinations):
                for destination in destinations:
                    if st.button(
                        SIDEBAR_LABELS[destination],
                        key=f"grouped_nav_{destination}",
                        icon=SIDEBAR_ICONS[destination],
                        disabled=page == destination,
                        width="stretch",
                    ):
                        st.session_state["_navigate_to"] = destination
                        st.rerun()

        secondary_pages = [item for pages in SIDEBAR_SECONDARY_GROUPS.values() for item in pages]
        with st.expander("Mais ferramentas", expanded=page in secondary_pages):
            for section_name, destinations in SIDEBAR_SECONDARY_GROUPS.items():
                st.caption(section_name.upper())
                for destination in destinations:
                    if st.button(
                        SIDEBAR_LABELS[destination],
                        key=f"secondary_nav_{destination}",
                        icon=SIDEBAR_ICONS[destination],
                        disabled=page == destination,
                        width="stretch",
                    ):
                        st.session_state["_navigate_to"] = destination
                        st.rerun()

        setup_progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))
'''
if needle not in text:
    raise RuntimeError("Sidebar render loop not found")
text = text.replace(needle, replacement, 1)

# Primeiros Passos continua acessível pelo botão contextual de configuração,
# evitando ocupar espaço fixo na navegação principal.
path.write_text(text, encoding="utf-8")
print("UX V2 navigation applied")
