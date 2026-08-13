from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

# Insert theme state before CSS block.
marker = 'init_db()\n\nst.markdown("""\n<style>'
if marker in s:
    replacement = '''init_db()\n\nif "ui_theme" not in st.session_state:\n    st.session_state["ui_theme"] = "Claro"\n\nUI_THEME = st.session_state["ui_theme"]\nIS_DARK = UI_THEME == "Escuro"\nPLOT_TEMPLATE = "plotly_dark" if IS_DARK else "plotly_white"\n\nTHEME = {\n    "bg": "#0b1020" if IS_DARK else "#f5f7fb",\n    "surface": "#111827" if IS_DARK else "#ffffff",\n    "surface2": "#182235" if IS_DARK else "#f8fafc",\n    "sidebar": "#0f172a" if IS_DARK else "#ffffff",\n    "text": "#f8fafc" if IS_DARK else "#172033",\n    "muted": "#94a3b8" if IS_DARK else "#667085",\n    "border": "#263349" if IS_DARK else "#e4e9f1",\n    "primary": "#3b82f6" if IS_DARK else "#2563eb",\n    "primary_soft": "#172554" if IS_DARK else "#eff6ff",\n    "input": "#111827" if IS_DARK else "#ffffff",\n    "shadow": "0 8px 24px rgba(0,0,0,.18)" if IS_DARK else "0 5px 18px rgba(16,24,40,.05)",\n}\n\nst.markdown(f"""\n<style>'''
    s = s.replace(marker, replacement, 1)

# Replace full current CSS content with dynamic theme CSS.
start = s.find('st.markdown(f"""\n<style>')
if start == -1:
    start = s.find('st.markdown("""\n<style>')
end_token = '</style>\n""", unsafe_allow_html=True)'
end = s.find(end_token, start)
if start != -1 and end != -1:
    end += len(end_token)
    css = '''st.markdown(f"""
<style>
:root{{--rz-primary:{THEME['primary']};--rz-bg:{THEME['bg']};--rz-surface:{THEME['surface']};--rz-text:{THEME['text']};--rz-muted:{THEME['muted']};--rz-border:{THEME['border']}}}
html,body,[class*="css"]{{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.stApp{{background:{THEME['bg']};color:{THEME['text']}}}
[data-testid="stHeader"]{{background:{THEME['bg']};border-bottom:1px solid {THEME['border']}}}
[data-testid="stSidebar"]{{background:{THEME['sidebar']};border-right:1px solid {THEME['border']}}}
[data-testid="stSidebar"] .block-container{{padding-top:1.15rem}}
.block-container{{padding-top:1.1rem;padding-bottom:2.5rem;max-width:1240px}}
h1,h2,h3,h4,p,span,label{{color:{THEME['text']}}}
[data-testid="stCaptionContainer"],.stCaption{{color:{THEME['muted']}!important}}
[data-testid="stMetric"]{{background:{THEME['surface']};border:1px solid {THEME['border']};border-radius:14px;padding:15px 17px;box-shadow:{THEME['shadow']}}}
[data-testid="stMetricLabel"] p{{color:{THEME['muted']}!important;font-size:.82rem}}
[data-testid="stMetricValue"]{{color:{THEME['text']}!important;font-size:1.5rem;font-weight:760}}
.rz-brand{{font-size:1.45rem;font-weight:900;color:{THEME['text']};letter-spacing:-.045em}}.rz-brand span{{color:{THEME['primary']}}}
.rz-kicker{{color:{THEME['primary']};font-weight:750;font-size:.7rem;margin-bottom:.12rem;text-transform:uppercase;letter-spacing:.08em}}
.rz-title{{font-size:1.72rem;font-weight:820;color:{THEME['text']};margin:.05rem 0 .18rem;letter-spacing:-.035em}}
.rz-sub{{color:{THEME['muted']};margin-bottom:1.15rem;font-size:.93rem}}
.rz-section{{font-size:1.02rem;font-weight:760;color:{THEME['text']};margin:1.05rem 0 .62rem}}
.rz-alert{{border-radius:11px;padding:12px 14px;margin-bottom:8px;background:{THEME['surface']};border:1px solid {THEME['border']};box-shadow:{THEME['shadow']}}}
.rz-ok{{border-left:3px solid #12b76a}}.rz-info{{border-left:3px solid #2e90fa}}.rz-warn{{border-left:3px solid #f79009}}.rz-danger{{border-left:3px solid #f04438}}
.rz-small{{color:{THEME['muted']};font-size:.84rem;margin-top:2px}}
.rz-welcome{{background:linear-gradient(135deg,{THEME['primary']},#60a5fa);border:0;border-radius:16px;padding:18px 20px;margin-bottom:14px;box-shadow:{THEME['shadow']}}}
.rz-welcome-title{{font-size:1.08rem;font-weight:760;color:#fff}}.rz-welcome-sub{{color:#dbeafe;font-size:.86rem;margin-top:3px}}
div[data-testid="stButton"] button,div[data-testid="stFormSubmitButton"] button{{border-radius:9px;min-height:2.5rem;border:1px solid {THEME['border']};font-weight:650;background:{THEME['surface']};color:{THEME['text']}}}
div[data-testid="stButton"] button:hover,div[data-testid="stFormSubmitButton"] button:hover{{border-color:{THEME['primary']};color:{THEME['primary']}}}
div[data-testid="stDataFrame"]{{border:1px solid {THEME['border']};border-radius:11px;overflow:hidden;background:{THEME['surface']}}}
[data-testid="stExpander"]{{background:{THEME['surface']};border:1px solid {THEME['border']};border-radius:11px}}
[data-baseweb="select"]>div,[data-baseweb="input"]>div,input,textarea{{background:{THEME['input']}!important;color:{THEME['text']}!important;border-color:{THEME['border']}!important}}
[data-baseweb="popover"] [role="listbox"]{{background:{THEME['surface']}!important;color:{THEME['text']}!important}}
[data-baseweb="popover"] li{{background:{THEME['surface']}!important;color:{THEME['text']}!important}}
[data-testid="stSidebar"] [data-testid="stRadio"] label{{padding:.28rem .45rem;border-radius:8px}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover{{background:{THEME['primary_soft']}}}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked){{background:{THEME['primary_soft']}}}
[data-testid="stProgressBar"]>div>div{{background:{THEME['primary']}!important}}
hr{{border-color:{THEME['border']}}}
</style>
""", unsafe_allow_html=True)'''
    s = s[:start] + css + s[end:]

# Add theme selector in sidebar below brand caption.
needle = '''    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)\n    st.caption("Gestão simples para MEI")\n    st.divider()'''
replace = '''    st.markdown('<div class="rz-brand">RAZYNC <span>PRO</span></div>', unsafe_allow_html=True)\n    st.caption("Gestão simples para MEI")\n    st.selectbox("Tema", ["Claro", "Escuro"], key="ui_theme", label_visibility="collapsed")\n    st.divider()'''
if needle in s:
    s = s.replace(needle, replace, 1)

# Ensure plotly charts follow theme.
s = s.replace('fig.update_layout(height=', 'fig.update_layout(template=PLOT_TEMPLATE,height=')
s = s.replace('fig2.update_layout(height=', 'fig2.update_layout(template=PLOT_TEMPLATE,height=')

p.write_text(s, encoding='utf-8')
print('theme switcher applied')
# trigger workflow
