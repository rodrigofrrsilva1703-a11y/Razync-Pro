from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Remove dependencias do favicon quebrado e restaura um favicon seguro.
s = s.replace('from PIL import Image\n', '')
s = s.replace('from io import BytesIO\n', '')

start = s.find('with Image.open("assets/rz-logo.png") as _rz_source:')
end_marker = 'st.set_page_config(page_title="Razync Pro", page_icon=RAZYNC_ICON, layout="wide", initial_sidebar_state="expanded")'
if start != -1:
    end = s.find(end_marker, start)
    if end != -1:
        end += len(end_marker)
        s = s[:start] + 'st.set_page_config(page_title="Razync Pro", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")' + s[end:]
else:
    direct = 'RAZYNC_ICON = Image.open("assets/rz-logo.png")\nst.set_page_config(page_title="Razync Pro", page_icon=RAZYNC_ICON, layout="wide", initial_sidebar_state="expanded")'
    s = s.replace(direct, 'st.set_page_config(page_title="Razync Pro", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")', 1)

# Remove apenas a imagem quebrada da sidebar; preserva toda a navegacao.
s = s.replace('    st.image("assets/rz-logo.png", width=92)\n', '')

p.write_text(s, encoding='utf-8')
print('App restaurado sem depender do arquivo de logo corrompido.')
