from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Usa a logo RZ real na barra lateral e cria um favicon PNG normalizado em memória.
if 'from PIL import Image' not in s:
    s = s.replace('import streamlit as st\n', 'import streamlit as st\nfrom PIL import Image\n', 1)
if 'from io import BytesIO' not in s:
    s = s.replace('from PIL import Image\n', 'from PIL import Image\nfrom io import BytesIO\n', 1)

old_direct = 'RAZYNC_ICON = Image.open("assets/rz-logo.png")\nst.set_page_config(page_title="Razync Pro", page_icon=RAZYNC_ICON, layout="wide", initial_sidebar_state="expanded")'
old_emoji = 'st.set_page_config(page_title="Razync Pro", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")'
new_cfg = '''with Image.open("assets/rz-logo.png") as _rz_source:
    _rz_icon = _rz_source.copy()
_rz_icon.thumbnail((256, 256))
if _rz_icon.mode not in ("RGB", "RGBA"):
    _rz_icon = _rz_icon.convert("RGBA")
_rz_icon_buffer = BytesIO()
_rz_icon.save(_rz_icon_buffer, format="PNG", optimize=True)
RAZYNC_ICON = _rz_icon_buffer.getvalue()
st.set_page_config(page_title="Razync Pro", page_icon=RAZYNC_ICON, layout="wide", initial_sidebar_state="expanded")'''
if old_direct in s:
    s = s.replace(old_direct, new_cfg, 1)
elif old_emoji in s:
    s = s.replace(old_emoji, new_cfg, 1)

old_brand = 'with st.sidebar:\n    st.markdown("### RAZYNC PRO")'
new_brand = 'with st.sidebar:\n    st.image("assets/rz-logo.png", width=92)\n    st.markdown("### RAZYNC PRO")'
if old_brand in s:
    s = s.replace(old_brand, new_brand, 1)

p.write_text(s, encoding='utf-8')
print('Logo RZ mantida na lateral e favicon normalizado para PNG.')
