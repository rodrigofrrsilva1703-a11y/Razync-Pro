from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

repls = {
    '"bg": "#0b1020" if IS_DARK else "#f5f7fb",': '"bg": "#0b1020" if IS_DARK else "#f8fafc",',
    '"surface2": "#182235" if IS_DARK else "#f8fafc",': '"surface2": "#182235" if IS_DARK else "#f1f5f9",',
    '"sidebar": "#0f172a" if IS_DARK else "#ffffff",': '"sidebar": "#0f172a" if IS_DARK else "#f8fafc",',
    '"text": "#f8fafc" if IS_DARK else "#172033",': '"text": "#f8fafc" if IS_DARK else "#0f172a",',
    '"muted": "#94a3b8" if IS_DARK else "#667085",': '"muted": "#94a3b8" if IS_DARK else "#64748b",',
    '"border": "#263349" if IS_DARK else "#e4e9f1",': '"border": "#263349" if IS_DARK else "#dbe3ed",',
    '"primary": "#3b82f6" if IS_DARK else "#2563eb",': '"primary": "#3b82f6" if IS_DARK else "#1d4ed8",',
    '"primary_soft": "#172554" if IS_DARK else "#eff6ff",': '"primary_soft": "#172554" if IS_DARK else "#eaf2ff",',
    '"shadow": "0 8px 24px rgba(0,0,0,.18)" if IS_DARK else "0 5px 18px rgba(16,24,40,.05)",': '"shadow": "0 8px 24px rgba(0,0,0,.18)" if IS_DARK else "0 2px 8px rgba(15,23,42,.045)",',
}
for old,new in repls.items():
    s=s.replace(old,new,1)

if '"hero_bg":' not in s:
    needle='''    "shadow": "0 8px 24px rgba(0,0,0,.18)" if IS_DARK else "0 2px 8px rgba(15,23,42,.045)",\n}'''
    replacement='''    "shadow": "0 8px 24px rgba(0,0,0,.18)" if IS_DARK else "0 2px 8px rgba(15,23,42,.045)",\n    "hero_bg": "linear-gradient(135deg,#1d4ed8,#2563eb)" if IS_DARK else "#ffffff",\n    "hero_text": "#ffffff" if IS_DARK else "#0f172a",\n    "hero_sub": "#dbeafe" if IS_DARK else "#64748b",\n    "hero_border": "transparent" if IS_DARK else "#cfe0fb",\n}'''
    s=s.replace(needle,replacement,1)

s=s.replace(
    '.rz-welcome{{background:linear-gradient(135deg,{THEME[\'primary\']},#60a5fa);border:0;border-radius:16px;padding:18px 20px;margin-bottom:14px;box-shadow:{THEME[\'shadow\']}}}',
    '.rz-welcome{{background:{THEME[\'hero_bg\']};border:1px solid {THEME[\'hero_border\']};border-left:4px solid {THEME[\'primary\']};border-radius:14px;padding:17px 19px;margin-bottom:14px;box-shadow:{THEME[\'shadow\']}}}',
    1,
)
s=s.replace(
    '.rz-welcome-title{{font-size:1.08rem;font-weight:760;color:#fff}}.rz-welcome-sub{{color:#dbeafe;font-size:.86rem;margin-top:3px}}',
    '.rz-welcome-title{{font-size:1.08rem;font-weight:760;color:{THEME[\'hero_text\']}}}.rz-welcome-sub{{color:{THEME[\'hero_sub\']};font-size:.86rem;margin-top:3px}}',
    1,
)

# Sidebar spacing and light-theme hierarchy.
extra='''\n[data-testid="stSidebar"] [data-baseweb="select"]>div{{background:{THEME['surface']}!important;border:1px solid {THEME['border']}!important}}\n[data-testid="stSidebar"] hr{{margin:.8rem 0}}\n[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p{{color:{THEME['primary']}!important;font-weight:700}}\n[data-testid="stSidebar"] [data-testid="stRadio"] label{{margin-bottom:2px}}\n[data-testid="stSidebar"] .stCaption{{color:{THEME['muted']}!important}}\n'''
anchor='hr{{border-color:{THEME[\'border\']}}}'
if extra.strip() not in s:
    s=s.replace(anchor, anchor+extra,1)

# Cleaner light cards and section rhythm.
s=s.replace('border-radius:14px;padding:15px 17px;box-shadow:{THEME[\'shadow\']}', 'border-radius:12px;padding:15px 17px;box-shadow:{THEME[\'shadow\']}',1)
s=s.replace('.rz-section{{font-size:1.02rem;font-weight:760;color:{THEME[\'text\']};margin:1.05rem 0 .62rem}}', '.rz-section{{font-size:.98rem;font-weight:760;color:{THEME[\'text\']};margin:1.2rem 0 .58rem}}',1)

p.write_text(s, encoding='utf-8')
print('light theme refined')
