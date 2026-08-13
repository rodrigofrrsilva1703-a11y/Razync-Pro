from pathlib import Path

# Razync Pro V16 — identidade visual alinhada ao produto Razync.
# IMPORTANTE: este script atua somente neste repositório Razync-Pro.

# ---------- ui_system.py ----------
p = Path('ui_system.py')
s = p.read_text(encoding='utf-8')

replacements = {
    '"bg": "#f6f8fc"': '"bg": "#f5f9fb"',
    '"surface_soft": "#eef3f9"': '"surface_soft": "#edf6f9"',
    '"sidebar": "#f8faff"': '"sidebar": "#f7fbfc"',
    '"text": "#334155"': '"text": "#1d2a33"',
    '"muted": "#718096"': '"muted": "#71818d"',
    '"border": "#dce5f0"': '"border": "#d7e5ea"',
    '"primary": "#4f7fc9"': '"primary": "#0eaedb"',
    '"primary_hover": "#3f6fb7"': '"primary_hover": "#0b95bd"',
    '"primary_soft": "#eaf2fc"': '"primary_soft": "#e4f7fc"',
    '"bg": "#0d1422"': '"bg": "#0b0f13"',
    '"surface": "#151f31"': '"surface": "#111820"',
    '"surface_soft": "#1b2940"': '"surface_soft": "#16212b"',
    '"sidebar": "#101a2b"': '"sidebar": "#0e141a"',
    '"text": "#e8eef7"': '"text": "#f4f7fa"',
    '"muted": "#9aabc2"': '"muted": "#94a4b3"',
    '"border": "#2a3a54"': '"border": "#27333e"',
    '"primary": "#6ea2f2"': '"primary": "#13b9e8"',
    '"primary_hover": "#8ab5f6"': '"primary_hover": "#42c9ee"',
    '"primary_soft": "#1a3152"': '"primary_soft": "rgba(19,185,232,.12)"',
}
for old, new in replacements.items():
    s = s.replace(old, new)

# Corrige também overrides hardcoded mais importantes dos temas.
for old, new in {
    '#0d1422':'#0b0f13', '#101a2b':'#0e141a', '#151f31':'#111820', '#1b2940':'#16212b',
    '#2a3a54':'#27333e', '#6ea2f2':'#13b9e8', '#8ab5f6':'#42c9ee', '#5e91dd':'#13b9e8',
    '#4f8ee8':'#13b9e8', '#7fb2ff':'#55d0f1', '#79aef8':'#55d0f1', '#8fc0ff':'#55d0f1',
    '#f6f8fc':'#f5f9fb', '#f8faff':'#f7fbfc', '#eef3f9':'#edf6f9', '#4f7fc9':'#0eaedb',
    '#3f6fb7':'#0b95bd', '#eaf2fc':'#e4f7fc'
}.items():
    s = s.replace(old, new)

# Refinamento visual de marca na sidebar.
old_css = '''.rz-brand-wrap { padding:.55rem .2rem .7rem; }\n.rz-brand { font-size:1.48rem; line-height:1; font-weight:900; letter-spacing:-.055em; color:var(--rz-text); }\n.rz-brand span { color:var(--rz-primary); }\n.rz-brand-sub { margin-top:.38rem; font-size:.77rem; color:var(--rz-muted); }'''
new_css = '''.rz-brand-wrap { padding:.6rem .15rem .85rem; }\n.rz-brand-lockup { display:flex; align-items:center; gap:.72rem; }\n.rz-brand-mark { width:38px; height:38px; border-radius:11px; display:grid; place-items:center; background:linear-gradient(145deg, rgba(19,185,232,.18), rgba(19,185,232,.055)); border:1px solid rgba(19,185,232,.38); box-shadow:inset 0 0 0 1px rgba(255,255,255,.025); }\n.rz-brand-mark svg { width:24px; height:24px; color:var(--rz-primary)!important; fill:none!important; }\n.rz-brand-copy { min-width:0; }\n.rz-brand { font-size:1.42rem; line-height:1; font-weight:900; letter-spacing:-.052em; color:var(--rz-text); }\n.rz-brand span { color:var(--rz-primary); font-size:.72rem; letter-spacing:.08em; margin-left:.25rem; vertical-align:.18rem; }\n.rz-brand-sub { margin-top:.38rem; font-size:.73rem; color:var(--rz-muted); }'''
if old_css in s:
    s = s.replace(old_css, new_css, 1)

# Cards e focos com assinatura cyan do grupo, sem descaracterizar tema claro.
s = s.replace('.rz-business:before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--rz-primary); }',
              '.rz-business:before { content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:linear-gradient(180deg,var(--rz-primary),rgba(19,185,232,.35)); }')

p.write_text(s, encoding='utf-8')

# ---------- app.py ----------
p = Path('app.py')
s = p.read_text(encoding='utf-8')
old_brand = '''    st.markdown('<div class="rz-brand-wrap"><div class="rz-brand">RAZYNC <span>PRO</span></div><div class="rz-brand-sub">Contabilidade simples para MEI</div></div>', unsafe_allow_html=True)'''
new_brand = '''    st.markdown('''\n    <div class="rz-brand-wrap">\n      <div class="rz-brand-lockup">\n        <div class="rz-brand-mark" aria-hidden="true">\n          <svg viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">\n            <path d="M6.3 8.1 14 3.7l7.7 4.4v8.8L14 21.3l-7.7-4.4V8.1Z" stroke="currentColor" stroke-width="1.8"/>\n            <path d="M9.6 10.1 14 7.6l4.4 2.5v5L14 17.6l-4.4-2.5v-5Z" stroke="currentColor" stroke-width="1.8"/>\n            <circle cx="14" cy="12.6" r="1.45" fill="currentColor" stroke="none"/>\n            <path d="M14 3.7v3.9M21.7 8.1l-3.3 2M6.3 8.1l3.3 2M14 17.6v3.7" stroke="currentColor" stroke-width="1.55" stroke-linecap="round"/>\n          </svg>\n        </div>\n        <div class="rz-brand-copy">\n          <div class="rz-brand">RAZYNC <span>PRO</span></div>\n          <div class="rz-brand-sub">Contabilidade simples para MEI</div>\n        </div>\n      </div>\n    </div>''', unsafe_allow_html=True)'''
if old_brand in s:
    s = s.replace(old_brand, new_brand, 1)

p.write_text(s, encoding='utf-8')
print('Identidade Razync aplicada somente ao Razync-Pro')
