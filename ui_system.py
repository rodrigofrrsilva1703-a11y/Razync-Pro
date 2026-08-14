from __future__ import annotations

import streamlit as st

# Identidade compartilhada do grupo Razync.
# Referência visual: Razync usa #0b0f13, #111820, #27333e e cyan #13b9e8.
THEMES = {
    "Claro": {
        "bg": "#f5f9fb",
        "surface": "#ffffff",
        "surface_soft": "#edf6f9",
        "sidebar": "#f7fbfc",
        "text": "#1d2a33",
        "muted": "#71818d",
        "border": "#d7e5ea",
        "primary": "#0eaedb",
        "primary_hover": "#0b95bd",
        "primary_soft": "#e4f7fc",
        "success": "#3f8f69",
        "warning": "#b9853d",
        "danger": "#c65f67",
        "shadow": "0 8px 28px rgba(38, 63, 76, .055)",
        "shadow_soft": "0 2px 10px rgba(38, 63, 76, .04)",
        "plot": "plotly_white",
    },
    "Escuro": {
        "bg": "#0b0f13",
        "surface": "#111820",
        "surface_soft": "#16212b",
        "sidebar": "#0e141a",
        "text": "#f4f7fa",
        "muted": "#94a4b3",
        "border": "#27333e",
        "primary": "#13b9e8",
        "primary_hover": "#42c9ee",
        "primary_soft": "rgba(19, 185, 232, .12)",
        "success": "#56b98b",
        "warning": "#d4a457",
        "danger": "#df7b82",
        "shadow": "0 12px 34px rgba(0, 0, 0, .24)",
        "shadow_soft": "0 4px 16px rgba(0, 0, 0, .16)",
        "plot": "plotly_dark",
    },
}


def tokens(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES["Claro"])


def inject_design_system(theme_name: str) -> None:
    t = tokens(theme_name)
    dark = theme_name == "Escuro"

    if dark:
        native = """
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#0b0f13 !important; color:#f4f7fa !important; }
[data-testid="stHeader"] { background:#0b0f13 !important; border-bottom:1px solid #202a33 !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#0e141a !important; border-right:1px solid #27333e !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#111820 !important; border-color:#27333e !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#111820 !important; color:#f4f7fa !important; border-color:#33424f !important; box-shadow:none !important; }
input::placeholder, textarea::placeholder { color:#758796 !important; opacity:1 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#111820 !important; color:#f4f7fa !important; border-color:#33424f !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background:#162a35 !important; color:#ffffff !important; }
button:not([kind="primary"]) { background:#111820 !important; color:#dce5eb !important; border-color:#33424f !important; box-shadow:none !important; }
button:not([kind="primary"]):hover { background:#16212b !important; color:#42c9ee !important; border-color:#13b9e8 !important; }
button[kind="primary"] { background:#13b9e8 !important; color:#071017 !important; border-color:#13b9e8 !important; font-weight:750 !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; border-color:transparent !important; color:#dce5eb !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:rgba(19,185,232,.10) !important; color:#42c9ee !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:rgba(19,185,232,.08) !important; }
[data-testid="stFileUploaderDropzone"] { background:#111820 !important; border-color:#33424f !important; }
[data-testid="stFileUploaderDropzone"] * { color:#aebdc8 !important; }
[data-testid="stTabs"] button { color:#94a4b3 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#42c9ee !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p, label, p, span { color:#dce5eb !important; }
h1,h2,h3,h4,h5,h6 { color:#f4f7fa !important; }
small,[data-testid="stCaptionContainer"],.stCaption { color:#94a4b3 !important; }
[data-testid="stProgressBar"] > div { background:#1b2730 !important; }
[data-testid="stProgressBar"] > div > div { background:#13b9e8 !important; }
hr { border-color:#27333e !important; }
"""
    else:
        native = """
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#f5f9fb !important; color:#1d2a33 !important; }
[data-testid="stHeader"] { background:#f5f9fb !important; border-bottom:1px solid #e1ebef !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#f7fbfc !important; border-right:1px solid #d7e5ea !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#ffffff !important; border-color:#d7e5ea !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#ffffff !important; color:#1d2a33 !important; border-color:#d7e5ea !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#ffffff !important; color:#1d2a33 !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background:#e4f7fc !important; color:#0b7897 !important; }
button:not([kind="primary"]) { background:#ffffff !important; color:#344650 !important; border-color:#d7e5ea !important; box-shadow:none !important; }
button:not([kind="primary"]):hover { background:#edf6f9 !important; color:#0b95bd !important; border-color:#8ad9eb !important; }
button[kind="primary"] { background:#0eaedb !important; color:#ffffff !important; border-color:#0eaedb !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:#e4f7fc !important; color:#0b95bd !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#edf6f9 !important; }
[data-testid="stFileUploaderDropzone"] { background:#f7fbfc !important; border-color:#d7e5ea !important; }
[data-testid="stFileUploaderDropzone"] * { color:#536772 !important; }
[data-testid="stTabs"] button { color:#71818d !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#0eaedb !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p { color:#344650 !important; }
h1,h2,h3,h4,h5,h6 { color:#1d2a33 !important; }
small,[data-testid="stCaptionContainer"],.stCaption { color:#71818d !important; }
[data-testid="stProgressBar"] > div > div { background:#0eaedb !important; }
hr { border-color:#d7e5ea !important; }
"""

    st.markdown(
        f"""
<style>
:root {{
  --rz-bg:{t['bg']};
  --rz-surface:{t['surface']};
  --rz-soft:{t['surface_soft']};
  --rz-text:{t['text']};
  --rz-muted:{t['muted']};
  --rz-border:{t['border']};
  --rz-primary:{t['primary']};
  --rz-primary-soft:{t['primary_soft']};
  --rz-shadow:{t['shadow']};
  --rz-shadow-soft:{t['shadow_soft']};
}}
html, body, [class*="css"] {{ font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.stApp {{ background:var(--rz-bg); color:var(--rz-text); }}
[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}
[data-testid="stSidebar"] {{ background:{t['sidebar']}; border-right:1px solid var(--rz-border); }}
[data-testid="stSidebar"] > div:first-child {{ padding-top:.55rem; }}
.block-container {{ max-width:1320px; padding-top:1.25rem; padding-bottom:3rem; }}

/* Lockup do grupo: símbolo visual + wordmark Razync Pro. */
.rz-brand-wrap {{ padding:.62rem .18rem .86rem 3.1rem; position:relative; min-height:48px; }}
.rz-brand-wrap::before {{
  content:""; position:absolute; left:.18rem; top:.34rem; width:38px; height:38px; border-radius:11px;
  background:
    linear-gradient(30deg, transparent 44%, var(--rz-primary) 45%, var(--rz-primary) 51%, transparent 52%),
    linear-gradient(150deg, transparent 44%, var(--rz-primary) 45%, var(--rz-primary) 51%, transparent 52%),
    radial-gradient(circle at center, var(--rz-primary) 0 3px, transparent 4px),
    linear-gradient(145deg, rgba(19,185,232,.18), rgba(19,185,232,.045));
  border:1px solid rgba(19,185,232,.42);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.025), 0 5px 16px rgba(19,185,232,.08);
}}
.rz-brand {{ font-size:1.44rem; line-height:1; font-weight:900; letter-spacing:-.052em; color:var(--rz-text); }}
.rz-brand span {{ color:var(--rz-primary); font-size:.72rem; letter-spacing:.09em; margin-left:.22rem; vertical-align:.18rem; }}
.rz-brand-sub {{ margin-top:.38rem; font-size:.73rem; color:var(--rz-muted); }}

h1,h2,h3,h4,p,label,span {{ color:var(--rz-text); }}
small,[data-testid="stCaptionContainer"],.stCaption {{ color:var(--rz-muted)!important; }}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label {{ color:var(--rz-text)!important; }}
[data-testid="stSidebar"] small,[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:var(--rz-muted)!important; }}
[data-testid="stMarkdownContainer"] a {{ color:var(--rz-primary)!important; }}
[data-testid="stWidgetLabel"] p {{ color:var(--rz-text)!important; }}

.rz-eyebrow {{ color:var(--rz-primary); font-weight:780; font-size:.68rem; text-transform:uppercase; letter-spacing:.11em; margin-bottom:.25rem; }}
.rz-page-title {{ font-size:1.78rem; line-height:1.15; font-weight:820; letter-spacing:-.04em; color:var(--rz-text); }}
.rz-page-sub {{ font-size:.93rem; color:var(--rz-muted); margin-top:.3rem; margin-bottom:1.25rem; max-width:760px; }}
.rz-section-title {{ font-size:1rem; font-weight:760; color:var(--rz-text); margin:.45rem 0 .7rem; }}
.rz-section-sub {{ font-size:.82rem; color:var(--rz-muted); margin-top:-.45rem; margin-bottom:.7rem; }}

.rz-business {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:14px; padding:17px 19px; box-shadow:var(--rz-shadow-soft); position:relative; overflow:hidden; }}
.rz-business:before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:linear-gradient(180deg,var(--rz-primary),rgba(19,185,232,.3)); }}
.rz-business-name {{ font-size:1.05rem; font-weight:780; color:var(--rz-text); }}
.rz-business-meta {{ font-size:.8rem; color:var(--rz-muted); margin-top:4px; }}

[data-testid="stMetric"] {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:13px; padding:16px 17px; box-shadow:var(--rz-shadow-soft); min-height:105px; }}
[data-testid="stMetricLabel"] p {{ color:var(--rz-muted)!important; font-size:.8rem; font-weight:650; }}
[data-testid="stMetricValue"] {{ color:var(--rz-text)!important; font-size:1.48rem; font-weight:800; letter-spacing:-.035em; }}

.rz-alert {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:11px; padding:12px 14px; margin-bottom:8px; box-shadow:var(--rz-shadow-soft); }}
.rz-alert-title {{ font-size:.9rem; font-weight:740; color:var(--rz-text); }}
.rz-alert-text {{ font-size:.8rem; color:var(--rz-muted); margin-top:3px; }}
.rz-alert.rz-danger {{ border-left:3px solid {t['danger']}; }}
.rz-alert.rz-warn {{ border-left:3px solid {t['warning']}; }}
.rz-alert.rz-info {{ border-left:3px solid {t['primary']}; }}
.rz-alert.rz-ok {{ border-left:3px solid {t['success']}; }}

.rz-empty {{ background:var(--rz-surface); border:1px dashed var(--rz-border); border-radius:13px; padding:28px 22px; text-align:center; box-shadow:var(--rz-shadow-soft); }}
.rz-empty-icon {{ color:var(--rz-primary); font-size:1.4rem; margin-bottom:7px; }}
.rz-empty-title {{ color:var(--rz-text); font-size:.94rem; font-weight:750; }}
.rz-empty-text {{ color:var(--rz-muted); font-size:.82rem; margin:5px auto 0; max-width:620px; line-height:1.5; }}
.rz-helper {{ background:var(--rz-primary-soft); border:1px solid rgba(19,185,232,.20); border-radius:10px; padding:10px 12px; color:var(--rz-muted); font-size:.8rem; }}

div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{ border-radius:9px; min-height:2.55rem; border:1px solid var(--rz-border); background:var(--rz-surface); color:var(--rz-text); font-weight:660; box-shadow:none; }}
div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {{ border-color:var(--rz-primary); color:var(--rz-primary); }}
div[data-testid="stFormSubmitButton"] button[kind="primary"], button[kind="primary"] {{ background:var(--rz-primary)!important; border-color:var(--rz-primary)!important; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, input, textarea {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; border-color:var(--rz-border)!important; border-radius:9px!important; }}
[data-testid="stDataFrame"] {{ border:1px solid var(--rz-border); border-radius:11px; overflow:hidden; background:var(--rz-surface); }}
[data-testid="stExpander"] {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:11px; box-shadow:var(--rz-shadow-soft); }}
[data-testid="stProgressBar"] > div > div {{ background:var(--rz-primary)!important; }}
hr {{ border-color:var(--rz-border); }}

.rz-sidebar-section {{ font-size:.67rem; font-weight:800; text-transform:uppercase; letter-spacing:.09em; color:var(--rz-muted); margin:.8rem .15rem .32rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] {{ box-shadow:none; border:0; background:transparent; border-radius:9px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] details {{ border:0; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{ border-radius:8px; padding:.32rem .4rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{ background:var(--rz-soft); }}
[data-testid="stSidebar"] [data-testid="stButton"] button {{ width:100%; min-height:2.25rem; text-align:left; justify-content:flex-start; padding:.35rem .65rem; border:0; background:transparent; box-shadow:none; }}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{ background:var(--rz-primary-soft); color:var(--rz-primary); }}
.rz-current-page {{ background:var(--rz-primary-soft); color:var(--rz-primary); border-radius:8px; padding:.55rem .7rem; font-weight:760; font-size:.86rem; margin-bottom:.3rem; }}
.rz-nav-label {{ font-size:.68rem; font-weight:760; text-transform:uppercase; letter-spacing:.08em; color:var(--rz-muted); margin:.45rem 0 .15rem; }}
.rz-dev {{ background:var(--rz-soft); border:1px solid var(--rz-border); border-radius:9px; padding:9px 10px; font-size:.72rem; color:var(--rz-muted); margin-top:.65rem; }}

/* Experiência pública de autenticação. O :has limita os estilos às telas sem sessão. */
.stApp:has(.rz-login-shell) [data-testid="stSidebar"] { display:none; }
.stApp:has(.rz-login-shell) [data-testid="stHeader"] { background:transparent!important; border-bottom:0!important; }
.stApp:has(.rz-login-shell) [data-testid="stMain"] {
  background:
    radial-gradient(circle at 15% 5%, rgba(14,174,219,.13), transparent 34rem),
    radial-gradient(circle at 88% 92%, rgba(19,185,232,.09), transparent 30rem),
    var(--rz-bg)!important;
}
.stApp:has(.rz-login-shell) .block-container { max-width:1120px; padding-top:clamp(2rem,6vh,5.5rem); }
.rz-login-shell { max-width:760px; margin:0 auto 2rem; text-align:center; }
.rz-login-brand { display:flex; align-items:center; justify-content:center; gap:.7rem; margin-bottom:2.1rem; }
.rz-login-brand strong { font-size:1.35rem; letter-spacing:-.045em; font-weight:900; }
.rz-login-brand span { color:var(--rz-primary); font-size:.62rem; font-weight:850; letter-spacing:.13em; margin-left:.3rem; vertical-align:.22rem; }
.rz-login-mark { width:36px; height:36px; border-radius:11px; border:1px solid rgba(19,185,232,.42);
  background:
    linear-gradient(30deg, transparent 44%, var(--rz-primary) 45% 51%, transparent 52%),
    linear-gradient(150deg, transparent 44%, var(--rz-primary) 45% 51%, transparent 52%),
    radial-gradient(circle, var(--rz-primary) 0 3px, transparent 4px),
    linear-gradient(145deg, rgba(19,185,232,.20), rgba(19,185,232,.04));
  box-shadow:0 10px 30px rgba(14,174,219,.14);
}
.rz-login-kicker { color:var(--rz-primary); font-size:.72rem; font-weight:820; letter-spacing:.13em; text-transform:uppercase; margin-bottom:.75rem; }
.rz-login-shell h1 { font-size:clamp(2.15rem,5vw,3.75rem); line-height:1.04; letter-spacing:-.055em; margin:0; font-weight:880; }
.rz-login-shell h1 em { color:var(--rz-primary); font-style:normal; }
.rz-login-lead { max-width:640px; margin:1.15rem auto 1rem; color:var(--rz-muted)!important; font-size:1rem; line-height:1.65; }
.rz-login-benefits { display:flex; justify-content:center; flex-wrap:wrap; gap:.55rem; }
.rz-login-benefits span { color:var(--rz-muted); background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:999px; padding:.42rem .72rem; font-size:.75rem; box-shadow:var(--rz-shadow-soft); }
.stApp:has(.rz-login-shell) [data-testid="stTabs"] { max-width:560px; margin:0 auto; background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:18px; padding:1rem 1.15rem 1.2rem; box-shadow:0 22px 65px rgba(29,42,51,.10); }
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tablist"] { gap:.25rem; background:var(--rz-soft); border-radius:11px; padding:.25rem; }
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] { flex:1; justify-content:center; border-radius:8px; min-height:2.45rem; }
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:var(--rz-surface); box-shadow:var(--rz-shadow-soft); }
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [data-testid="stForm"] { border:0!important; padding:.85rem 0 0; box-shadow:none!important; }
.stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button { min-height:2.85rem; font-weight:780; background:linear-gradient(135deg,var(--rz-primary),#087fa7)!important; color:white!important; border:0!important; box-shadow:0 10px 24px rgba(14,174,219,.20)!important; }
.stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button:hover { transform:translateY(-1px); box-shadow:0 13px 28px rgba(14,174,219,.28)!important; }
.stApp:has(.rz-login-shell) input { min-height:2.7rem; }
.stApp:has(.rz-login-shell) footer { display:none; }

{native}
@media (max-width:1000px) {{ .block-container {{ padding-left:1rem; padding-right:1rem; }} [data-testid="stMetric"] {{ min-height:96px; }} }}
@media (max-width:720px) {{ .rz-page-title {{ font-size:1.5rem; }} .block-container {{ padding-top:.7rem; }} .stApp:has(.rz-login-shell) .block-container {{ padding:.8rem .8rem 2rem; }} .rz-login-shell {{ margin-bottom:1.2rem; }} .rz-login-brand {{ margin-bottom:1.35rem; }} .rz-login-lead {{ font-size:.91rem; }} .rz-login-benefits {{ gap:.35rem; }} .rz-login-benefits span {{ font-size:.68rem; padding:.35rem .55rem; }} .stApp:has(.rz-login-shell) [data-testid="stTabs"] {{ padding:.7rem .75rem 1rem; border-radius:14px; }} .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] p {{ font-size:.78rem; }} }}
</style>
""",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "Razync Pro • MEI") -> None:
    st.markdown(f'<div class="rz-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rz-page-sub">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str, subtitle: str | None = None) -> None:
    st.markdown(f'<div class="rz-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="rz-section-sub">{subtitle}</div>', unsafe_allow_html=True)


def business_card(name: str, year: int, cnpj: str | None = None) -> None:
    meta = f"Ano {year}"
    if cnpj:
        meta += f" • CNPJ {cnpj}"
    st.markdown(
        f'<div class="rz-business"><div class="rz-business-name">{name}</div><div class="rz-business-meta">{meta} • visão consolidada financeira e fiscal</div></div>',
        unsafe_allow_html=True,
    )


def alert_card(level: str, title: str, text: str) -> None:
    cls = {"danger": "rz-danger", "warn": "rz-warn", "info": "rz-info", "ok": "rz-ok"}.get(level, "rz-info")
    st.markdown(
        f'<div class="rz-alert {cls}"><div class="rz-alert-title">{title}</div><div class="rz-alert-text">{text}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, text: str, icon: str = "○") -> None:
    st.markdown(
        f'<div class="rz-empty"><div class="rz-empty-icon">{icon}</div><div class="rz-empty-title">{title}</div><div class="rz-empty-text">{text}</div></div>',
        unsafe_allow_html=True,
    )


def helper_note(text: str) -> None:
    st.markdown(f'<div class="rz-helper">{text}</div>', unsafe_allow_html=True)


def apply_plot_theme(fig, theme_name: str, *, height: int | None = None) -> None:
    t = tokens(theme_name)
    dark = theme_name == "Escuro"
    grid = "#27333e" if dark else "#e2ecef"
    axis = "#52636f" if dark else "#c8d8de"
    hover_bg = "#111820" if dark else "#ffffff"
    hover_text = "#f4f7fa" if dark else "#1d2a33"
    hover_border = "#3b4b59" if dark else "#d7e5ea"
    colorway = [
        t["primary"],
        t["success"],
        t["warning"],
        t["danger"],
        "#8f83ea" if dark else "#7568cf",
        "#48aab9" if dark else "#3c92a0",
    ]
    kwargs = {
        "template": t["plot"],
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": t["text"], "family": "Inter, system-ui, sans-serif"},
        "margin": dict(l=8, r=8, t=18, b=8),
        "legend_title_text": "",
        "colorway": colorway,
        "hoverlabel": dict(
            bgcolor=hover_bg,
            bordercolor=hover_border,
            font=dict(color=hover_text, family="Inter, system-ui, sans-serif"),
        ),
    }
    if height:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=axis,
        tickcolor=axis,
        tickfont=dict(color=t["muted"]),
        title_font=dict(color=t["muted"]),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid,
        gridwidth=1,
        zeroline=False,
        linecolor=axis,
        tickcolor=axis,
        tickfont=dict(color=t["muted"]),
        title_font=dict(color=t["muted"]),
    )
