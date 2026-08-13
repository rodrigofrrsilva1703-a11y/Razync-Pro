from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Usa a logo RZ real como favicon e na barra lateral.
if 'from PIL import Image' not in s:
    s = s.replace('import streamlit as st\n', 'import streamlit as st\nfrom PIL import Image\n', 1)

old_cfg = 'st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")'
new_cfg = 'RAZYNC_ICON = Image.open("assets/rz-logo.png")\nst.set_page_config(page_title="Razync Pro", page_icon=RAZYNC_ICON, layout="wide", initial_sidebar_state="expanded")'
s = s.replace(old_cfg, new_cfg, 1)

old_brand = 'with st.sidebar:\n    st.markdown("### RAZYNC PRO")'
new_brand = 'with st.sidebar:\n    st.image("assets/rz-logo.png", width=92)\n    st.markdown("### RAZYNC PRO")'
s = s.replace(old_brand, new_brand, 1)

p.write_text(s, encoding='utf-8')
print('Logo RZ aplicada na lateral e favicon.')
