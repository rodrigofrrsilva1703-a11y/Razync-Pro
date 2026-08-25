from __future__ import annotations

import streamlit as st

# Identidade compartilhada do grupo Razync.
# Referência visual: Razync usa #07111b, #0d1824, #22384b e cyan #10bdf2.
THEMES = {
    "Claro": {
        "bg": "#f1f6fa",
        "surface": "#ffffff",
        "surface_soft": "#e4f2f8",
        "sidebar": "#f7fafc",
        "text": "#111c27",
        "muted": "#607487",
        "border": "#cfdee8",
        "control_border": "#aebfcb",
        "control_bg": "#f8fbfd",
        "primary": "#08b9ef",
        "primary_hover": "#009dce",
        "primary_soft": "#ddf6ff",
        "success": "#3f8f69",
        "warning": "#b9853d",
        "danger": "#c65f67",
        "shadow": "0 8px 28px rgba(38, 63, 76, .055)",
        "shadow_soft": "0 2px 10px rgba(38, 63, 76, .04)",
        "plot": "plotly_white",
    },
    "Escuro": {
        "bg": "#07111b",
        "surface": "#0d1824",
        "surface_soft": "#132232",
        "sidebar": "#09131e",
        "text": "#f5f9fc",
        "muted": "#91a7ba",
        "border": "#22384b",
        "control_border": "#385269",
        "control_bg": "#101d2a",
        "primary": "#10bdf2",
        "primary_hover": "#43cdf7",
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
    primary_contrast = "#06131c" if dark else "#ffffff"

    if dark:
        native = """
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#07111b !important; color:#f5f9fc !important; }
[data-testid="stHeader"] { background:#07111b !important; border-bottom:1px solid #1b3042 !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#09131e !important; border-right:1px solid #22384b !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#0d1824 !important; border-color:#22384b !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#0d1824 !important; color:#f5f9fc !important; border-color:#2c455a !important; box-shadow:none !important; }
input::placeholder, textarea::placeholder { color:#7890a4 !important; opacity:1 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#0d1824 !important; color:#f5f9fc !important; border-color:#2c455a !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background:#123044 !important; color:#ffffff !important; }
button:not([kind="primary"]) { background:#0d1824 !important; color:#dce8f1 !important; border-color:#2c455a !important; box-shadow:none !important; }
button:not([kind="primary"]):hover { background:#132232 !important; color:#43cdf7 !important; border-color:#10bdf2 !important; }
button[kind="primary"] { background:#10bdf2 !important; color:#04101a !important; border-color:#10bdf2 !important; font-weight:750 !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; border-color:transparent !important; color:#dce8f1 !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:rgba(16,189,242,.10) !important; color:#43cdf7 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:rgba(16,189,242,.08) !important; }
[data-testid="stFileUploaderDropzone"] { background:#0d1824 !important; border-color:#2c455a !important; }
[data-testid="stFileUploaderDropzone"] * { color:#aebdc8 !important; }
[data-testid="stTabs"] button { color:#91a7ba !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#43cdf7 !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p, label, p, span { color:#dce8f1 !important; }
h1,h2,h3,h4,h5,h6 { color:#f5f9fc !important; }
small,[data-testid="stCaptionContainer"],.stCaption { color:#91a7ba !important; }
[data-testid="stProgressBar"] > div { background:#122333 !important; }
[data-testid="stProgressBar"] > div > div { background:#10bdf2 !important; }
hr { border-color:#22384b !important; }
"""
    else:
        native = """
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#f1f6fa !important; color:#111c27 !important; }
[data-testid="stHeader"] { background:#f1f6fa !important; border-bottom:1px solid #dbe7ee !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#f7fafc !important; border-right:1px solid #cfdee8 !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#ffffff !important; border-color:#cfdee8 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#ffffff !important; color:#111c27 !important; border-color:#cfdee8 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#ffffff !important; color:#111c27 !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background:#ddf6ff !important; color:#007fa8 !important; }
button:not([kind="primary"]) { background:#ffffff !important; color:#314657 !important; border-color:#cfdee8 !important; box-shadow:none !important; }
button:not([kind="primary"]):hover { background:#e4f2f8 !important; color:#009dce !important; border-color:#75d9f5 !important; }
button[kind="primary"] { background:#08b9ef !important; color:#ffffff !important; border-color:#08b9ef !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:#ddf6ff !important; color:#009dce !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#e4f2f8 !important; }
[data-testid="stFileUploaderDropzone"] { background:#f7fafc !important; border-color:#cfdee8 !important; }
[data-testid="stFileUploaderDropzone"] * { color:#536b7e !important; }
[data-testid="stTabs"] button { color:#607487 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#08b9ef !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p { color:#314657 !important; }
h1,h2,h3,h4,h5,h6 { color:#111c27 !important; }
small,[data-testid="stCaptionContainer"],.stCaption { color:#607487 !important; }
[data-testid="stProgressBar"] > div > div { background:#08b9ef !important; }
hr { border-color:#cfdee8 !important; }
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
  --rz-control-border:{t['control_border']};
  --rz-control-bg:{t['control_bg']};
  --rz-primary:{t['primary']};
  --rz-primary-soft:{t['primary_soft']};
  --rz-success:{t['success']};
  --rz-danger:{t['danger']};
  --rz-shadow:{t['shadow']};
  --rz-shadow-soft:{t['shadow_soft']};
}}
html, body, [class*="css"] {{ font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none!important; }}
[data-testid="stToolbar"] {{ display:flex!important; background:transparent!important; }}
[data-testid="stToolbar"] button:not([data-testid="stExpandSidebarButton"]) {{ display:none!important; }}
:where(button, a, input, textarea, select, [role="tab"]):focus-visible {{ outline:3px solid color-mix(in srgb,var(--rz-primary) 50%,transparent)!important; outline-offset:2px; }}
@media (prefers-reduced-motion:reduce) {{ *, *::before, *::after {{ scroll-behavior:auto!important; transition:none!important; animation:none!important; }} }}
.stApp {{ background:var(--rz-bg); color:var(--rz-text); }}
[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}
[data-testid="stSidebar"] {{ background:{t['sidebar']}; border-right:1px solid var(--rz-border); }}
[data-testid="stSidebar"] > div:first-child {{ padding-top:.55rem; }}
[data-testid="stExpandSidebarButton"] {{
  position:fixed!important; left:.65rem!important; top:.65rem!important; z-index:9999!important;
  width:42px!important; height:42px!important; border-radius:11px!important;
  background:var(--rz-surface)!important; border:1px solid var(--rz-border)!important;
  box-shadow:var(--rz-shadow-soft)!important;
}}
[data-testid="stExpandSidebarButton"] span {{ color:var(--rz-primary)!important; }}
.block-container {{ max-width:1320px; padding-top:1.25rem; padding-bottom:3rem; }}

/* Lockup do grupo: símbolo visual + wordmark Razync Pro. */
.rz-brand-wrap {{ padding:.62rem .18rem .86rem 3.1rem; position:relative; min-height:48px; }}
.rz-brand-wrap::before {{
  content:""; position:absolute; left:.18rem; top:.34rem; width:38px; height:38px; border-radius:11px;
  background:
    linear-gradient(30deg, transparent 44%, var(--rz-primary) 45%, var(--rz-primary) 51%, transparent 52%),
    linear-gradient(150deg, transparent 44%, var(--rz-primary) 45%, var(--rz-primary) 51%, transparent 52%),
    radial-gradient(circle at center, var(--rz-primary) 0 3px, transparent 4px),
    linear-gradient(145deg, rgba(16,189,242,.18), rgba(16,189,242,.045));
  border:1px solid rgba(16,189,242,.42);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.025), 0 5px 16px rgba(16,189,242,.08);
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
.rz-routine-meta {{ display:flex; flex-wrap:wrap; gap:.45rem; margin:-.25rem 0 .75rem; }}
.rz-routine-meta span {{ background:var(--rz-soft); border:1px solid var(--rz-border); border-radius:999px; color:var(--rz-muted); font-size:.7rem; font-weight:700; padding:.34rem .58rem; }}
.rz-mobile-only {{ display:none; }}
.rz-mobile-list {{ display:grid; gap:.55rem; }}
.rz-mobile-card {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:11px; padding:.72rem .8rem; box-shadow:var(--rz-shadow-soft); }}
.rz-mobile-card-head {{ display:flex; align-items:center; justify-content:space-between; gap:.65rem; font-size:.76rem; color:var(--rz-muted); }}
.rz-mobile-card-title {{ font-size:.86rem; font-weight:750; margin:.3rem 0 .15rem; color:var(--rz-text); }}
.rz-mobile-card-meta {{ font-size:.72rem; color:var(--rz-muted); }}
.rz-status-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:.55rem; margin:.3rem 0 1rem; }}
.rz-status-step {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:11px; padding:.7rem .8rem; }}
.rz-status-step strong {{ display:block; font-size:.82rem; }}
.rz-status-step span {{ color:var(--rz-muted); font-size:.72rem; line-height:1.4; }}
.rz-status-step.is-done {{ border-left:3px solid {t['success']}; }}
.rz-status-step.is-pending {{ border-left:3px solid {t['warning']}; }}

.rz-business {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:14px; padding:17px 19px; box-shadow:var(--rz-shadow-soft); position:relative; overflow:hidden; }}
.rz-business:before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:linear-gradient(180deg,var(--rz-primary),rgba(16,189,242,.3)); }}
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
.rz-helper {{ background:var(--rz-primary-soft); border:1px solid rgba(16,189,242,.20); border-radius:10px; padding:10px 12px; color:var(--rz-muted); font-size:.8rem; }}

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
.stApp:has(.rz-login-shell) [data-testid="stSidebar"] {{ display:none; }}
.stApp:has(.rz-login-shell) [data-testid="stHeader"] {{ background:transparent!important; border-bottom:0!important; }}
.stApp:has(.rz-login-shell) [data-testid="stMain"] {{
  background:
    radial-gradient(circle at 8% 8%, rgba(8,185,239,.16), transparent 27rem),
    radial-gradient(circle at 92% 86%, rgba(8,127,167,.11), transparent 30rem),
    linear-gradient(160deg, var(--rz-bg) 0%, var(--rz-soft) 100%)!important;
}}
.stApp:has(.rz-login-shell) [data-testid="stMain"]::before {{
  content:""; position:fixed; inset:0; pointer-events:none; opacity:.28;
  background-image:linear-gradient(var(--rz-border) 1px,transparent 1px),linear-gradient(90deg,var(--rz-border) 1px,transparent 1px);
  background-size:54px 54px; mask-image:linear-gradient(to bottom,black,transparent 72%);
}}
.stApp:has(.rz-login-shell) .block-container {{ position:relative; z-index:1; max-width:1040px; padding-top:clamp(1.5rem,4.5vh,3.5rem); padding-bottom:2.5rem; }}
.rz-login-shell {{ max-width:780px; margin:0 auto 1.35rem; text-align:center; }}
.rz-login-brand {{ display:inline-flex; align-items:center; justify-content:center; gap:.68rem; margin-bottom:1.35rem; padding:.42rem .72rem .42rem .48rem; border:1px solid var(--rz-border); border-radius:999px; background:color-mix(in srgb,var(--rz-surface) 88%,transparent); box-shadow:var(--rz-shadow-soft); backdrop-filter:blur(12px); }}
.rz-login-brand strong {{ font-size:1.08rem; letter-spacing:-.045em; font-weight:900; }}
.rz-login-brand span {{ color:var(--rz-primary); font-size:.57rem; font-weight:850; letter-spacing:.13em; margin-left:.25rem; vertical-align:.17rem; }}
.rz-login-mark {{ width:32px; height:32px; display:block; object-fit:cover; border-radius:9px; border:1px solid rgba(16,189,242,.45);
  box-shadow:0 8px 24px rgba(8,185,239,.18);
}}
.rz-login-kicker {{ color:var(--rz-primary); font-size:.68rem; font-weight:850; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.65rem; }}
.rz-login-shell h1 {{ font-size:clamp(2rem,4.5vw,3.35rem); line-height:1.02; letter-spacing:-.055em; margin:0; font-weight:900; }}
.rz-login-shell h1 em {{ color:var(--rz-primary); font-style:normal; }}
.rz-login-lead {{ max-width:610px; margin:.9rem auto .9rem; color:var(--rz-muted)!important; font-size:.96rem; line-height:1.6; }}
.rz-login-benefits {{ display:flex; justify-content:center; flex-wrap:wrap; gap:.48rem; }}
.rz-login-benefits span {{ color:var(--rz-text); background:color-mix(in srgb,var(--rz-surface) 91%,transparent); border:1px solid var(--rz-border); border-radius:999px; padding:.42rem .68rem; font-size:.72rem; font-weight:650; box-shadow:var(--rz-shadow-soft); }}
.rz-login-benefits b {{ color:var(--rz-primary); font-size:.61rem; letter-spacing:.06em; margin-right:.25rem; }}
.rz-login-proof {{ display:flex; align-items:center; justify-content:center; gap:.62rem; color:var(--rz-muted); font-size:.68rem; margin-top:.72rem; }}
.rz-login-proof i {{ width:3px; height:3px; border-radius:50%; background:var(--rz-primary); }}
.stApp:has(.rz-login-shell) [data-testid="stTabs"] {{ max-width:520px; margin:0 auto; background:color-mix(in srgb,var(--rz-surface) 96%,transparent); border:1px solid var(--rz-border); border-radius:20px; padding:.82rem 1.15rem 1.05rem; box-shadow:0 24px 75px rgba(29,42,51,.13),0 2px 8px rgba(29,42,51,.05); backdrop-filter:blur(18px); }}
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tablist"] {{ gap:.2rem; background:var(--rz-soft); border:1px solid var(--rz-border); border-radius:11px; padding:.22rem; }}
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] {{ flex:1; justify-content:center; border-radius:8px; min-height:2.35rem; font-weight:680; }}
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{ color:var(--rz-primary)!important; background:var(--rz-surface); box-shadow:0 2px 7px rgba(29,42,51,.09); }}
.rz-auth-heading {{ text-align:left; padding:.85rem 0 .05rem; }}
.rz-auth-heading strong {{ display:block; color:var(--rz-text); font-size:1.18rem; letter-spacing:-.025em; margin-bottom:.18rem; }}
.rz-auth-heading span {{ color:var(--rz-muted); font-size:.79rem; }}
.stApp:has(.rz-login-shell) [data-testid="stTabs"] [data-testid="stForm"] {{ border:0!important; padding:.65rem 0 0; box-shadow:none!important; }}
.stApp:has(.rz-login-shell) [data-testid="stTextInput"] label p {{ font-size:.76rem; font-weight:720; color:var(--rz-text)!important; }}
.stApp:has(.rz-login-shell) [data-baseweb="input"] {{ background:var(--rz-soft)!important; border:1px solid var(--rz-border)!important; border-radius:10px!important; overflow:hidden; }}
.stApp:has(.rz-login-shell) input {{ min-height:2.75rem; border-radius:10px; background:transparent!important; padding-left:.78rem!important; }}
.stApp:has(.rz-login-shell) [data-baseweb="input"]:focus-within {{ border-color:var(--rz-primary)!important; box-shadow:0 0 0 3px rgba(8,185,239,.12)!important; }}
.stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button {{ min-height:2.85rem; border-radius:10px; font-weight:800; background:linear-gradient(135deg,var(--rz-primary),#087fa7)!important; color:white!important; border:0!important; box-shadow:0 10px 24px rgba(8,185,239,.22)!important; transition:transform .16s ease,box-shadow .16s ease; }}
.stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button p {{ color:white!important; }}
.stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button:hover {{ transform:translateY(-1px); box-shadow:0 14px 30px rgba(8,185,239,.30)!important; }}
.stApp:has(.rz-login-shell) [data-testid="stLinkButton"] a {{ min-height:2.85rem; display:flex; align-items:center; justify-content:center; border:0!important; background:linear-gradient(135deg,var(--rz-primary),#087fa7)!important; color:{primary_contrast}!important; font-weight:800; box-shadow:0 10px 24px rgba(8,185,239,.22)!important; }}
.stApp:has(.rz-login-shell) [data-testid="stLinkButton"] a p {{ color:{primary_contrast}!important; }}
.stApp:has(.rz-login-shell) [data-testid="stLinkButton"] a:hover {{ filter:brightness(1.04); transform:translateY(-1px); }}
.rz-login-security {{ max-width:520px; margin:.72rem auto 0; text-align:center; color:var(--rz-muted); font-size:.67rem; }}
.stApp:has(.rz-login-shell) footer {{ display:none; }}
.stApp:has(.rz-demo-shell) [data-testid="stHeader"] {{ background:transparent!important; border-bottom:0!important; }}
.stApp:has(.rz-demo-shell) [data-testid="stMain"] {{ background:linear-gradient(150deg,var(--rz-bg),var(--rz-soft))!important; }}
.rz-demo-shell {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.2rem 0 1rem; }}
.rz-demo-brand {{ font-size:1.18rem; font-weight:900; letter-spacing:-.04em; }}
.rz-demo-brand span {{ color:var(--rz-primary); font-size:.62rem; letter-spacing:.12em; margin-left:.25rem; }}
.rz-demo-badge {{ color:var(--rz-primary); background:var(--rz-primary-soft); border:1px solid color-mix(in srgb,var(--rz-primary) 28%,transparent); border-radius:999px; padding:.38rem .68rem; font-size:.7rem; font-weight:760; }}
.rz-next-action {{ background:linear-gradient(135deg,var(--rz-surface),var(--rz-soft)); border:1px solid var(--rz-border); border-left:4px solid var(--rz-primary); border-radius:14px; padding:15px 17px; box-shadow:var(--rz-shadow-soft); }}
.rz-next-action strong {{ display:block; font-size:.92rem; margin-bottom:.22rem; }}
.rz-next-action span {{ color:var(--rz-muted); font-size:.79rem; line-height:1.45; }}

{native}

/* Campos com limites claros em ambos os temas. Os seletores usam data-testid
   e data-baseweb, evitando classes internas geradas pelo Streamlit. */
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInputRootElement"],
[data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stNumberInputContainer"],
[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextArea"] [data-rac][role="group"],
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stSelectbox"] [data-rac][role="group"],
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-rac][role="group"] {{
  background:var(--rz-control-bg)!important;
  border:1px solid var(--rz-control-border)!important;
  border-radius:10px!important;
  box-shadow:0 1px 2px rgba(17,28,39,.045)!important;
  overflow:hidden;
  transition:border-color .16s ease,box-shadow .16s ease,background .16s ease;
}}
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTextArea"] textarea {{
  min-height:2.65rem;
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  color:var(--rz-text)!important;
}}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stDateInput"] [data-baseweb="input"]:focus-within,
[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
[data-testid="stTextArea"] [data-rac][role="group"]:focus-within,
[data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
[data-testid="stSelectbox"] [data-rac][role="group"]:focus-within,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:focus-within,
[data-testid="stMultiSelect"] [data-rac][role="group"]:focus-within {{
  background:var(--rz-surface)!important;
  border-color:var(--rz-primary)!important;
  box-shadow:0 0 0 3px color-mix(in srgb,var(--rz-primary) 13%,transparent)!important;
}}
[data-testid="stNumberInput"] button,
[data-testid="stDateInput"] button {{
  min-height:2.65rem!important;
  background:var(--rz-soft)!important;
  color:var(--rz-text)!important;
  border:0!important;
  border-left:1px solid var(--rz-control-border)!important;
  border-radius:0!important;
}}
[data-testid="stNumberInput"] button:hover,
[data-testid="stDateInput"] button:hover {{ background:var(--rz-primary-soft)!important; color:var(--rz-primary)!important; }}
[data-testid="stSelectbox"] [data-rac][role="group"] input,
[data-testid="stMultiSelect"] [data-rac][role="group"] input {{
  min-height:2.65rem!important;
  background:transparent!important;
  border:0!important;
  border-radius:0!important;
  color:var(--rz-text)!important;
}}
[data-testid="stSelectbox"] [data-rac][role="group"] button,
[data-testid="stMultiSelect"] [data-rac][role="group"] button {{
  min-height:2.65rem!important;
  background:transparent!important;
  color:var(--rz-text)!important;
  border:0!important;
  border-left:1px solid var(--rz-control-border)!important;
  border-radius:0!important;
}}
input::placeholder, textarea::placeholder {{ color:var(--rz-muted)!important; opacity:.82!important; }}
[data-testid="stExpander"] summary,
[data-testid="stExpanderDetails"] {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; }}
[data-testid="stExpander"] summary {{ border-radius:10px 10px 0 0!important; }}
[data-testid="stExpander"] summary * {{ color:var(--rz-text)!important; }}
[data-testid="stExpander"] summary:hover {{ background:var(--rz-soft)!important; }}

/* Tipo do novo lançamento: duas opções grandes, sem ambiguidade visual. */
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) [role="radiogroup"] {{
  display:flex!important;
  width:min(100%,520px)!important;
  gap:.35rem!important;
  padding:.28rem!important;
  background:var(--rz-soft)!important;
  border:1px solid var(--rz-control-border)!important;
  border-radius:12px!important;
}}
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button {{
  flex:1 1 0!important;
  min-height:2.65rem!important;
  padding:.5rem .9rem!important;
  background:var(--rz-surface)!important;
  color:var(--rz-text)!important;
  border:1px solid var(--rz-border)!important;
  border-radius:9px!important;
  box-shadow:none!important;
  font-weight:720!important;
}}
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button * {{ color:inherit!important; }}
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button:first-child:is([aria-checked="true"],[aria-pressed="true"],[aria-selected="true"]),
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button:first-child:is([data-active="true"],[data-selected="true"]) {{
  background:color-mix(in srgb,var(--rz-success) 14%,var(--rz-surface))!important;
  color:var(--rz-success)!important;
  border-color:var(--rz-success)!important;
  box-shadow:0 3px 10px color-mix(in srgb,var(--rz-success) 14%,transparent)!important;
}}
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button:last-child:is([aria-checked="true"],[aria-pressed="true"],[aria-selected="true"]),
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button:last-child:is([data-active="true"],[data-selected="true"]) {{
  background:color-mix(in srgb,var(--rz-danger) 13%,var(--rz-surface))!important;
  color:var(--rz-danger)!important;
  border-color:var(--rz-danger)!important;
  box-shadow:0 3px 10px color-mix(in srgb,var(--rz-danger) 13%,transparent)!important;
}}
.st-key-tx_type_new :is([data-testid="stButtonGroup"],[data-testid="stSegmentedControl"]) button:hover {{ border-color:var(--rz-primary)!important; }}
@media (max-width:1000px) {{ .block-container {{ padding-left:1rem; padding-right:1rem; }} [data-testid="stMetric"] {{ min-height:96px; }} }}
@media (max-width:720px) {{
  .rz-page-title {{ font-size:1.5rem; }}
  .block-container {{ padding:.7rem .72rem 4.5rem; }}
  [data-testid="stHorizontalBlock"] {{ gap:.55rem; }}
  [data-testid="column"] {{ min-width:100%!important; flex:1 1 100%!important; }}
  [data-testid="stMetric"] {{ min-height:88px; padding:12px 13px; }}
  [data-testid="stMetricValue"] {{ font-size:1.25rem; }}
  [data-testid="stDataFrame"] {{ max-width:calc(100vw - 1.44rem); overflow-x:auto; }}
  .stButton button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button {{ min-height:44px; }}
  .stApp:has(.rz-login-shell) .block-container {{ padding:.8rem .8rem 2rem; }}
  .rz-login-shell {{ margin-bottom:1.2rem; }} .rz-login-brand {{ margin-bottom:1.35rem; }}
  .rz-login-lead {{ font-size:.91rem; }} .rz-login-benefits {{ gap:.35rem; }}
  .rz-login-benefits span {{ font-size:.68rem; padding:.35rem .55rem; }}
  .stApp:has(.rz-login-shell) [data-testid="stTabs"] {{ padding:.7rem .75rem 1rem; border-radius:14px; }}
  .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] p {{ font-size:.78rem; }}
  [data-testid="stTabs"] [role="tablist"] {{ overflow-x:auto; scrollbar-width:thin; justify-content:flex-start; }}
  [data-testid="stTabs"] [role="tab"] {{ flex:0 0 auto; white-space:nowrap; }}
  [data-testid="stFileUploaderDropzone"] {{ padding:.75rem; }}
  [data-testid="stFileUploaderDropzone"] button {{ min-height:44px; }}
  [data-testid="stDataFrame"] > div {{ overflow-x:auto; }}
  .rz-business {{ padding:14px 15px; }}
  .rz-empty {{ padding:22px 14px; }}
  .rz-mobile-only {{ display:block; }}
  .st-key-recent_desktop {{ display:none; }}
  .rz-status-grid {{ grid-template-columns:1fr; }}
  .rz-routine-meta {{ gap:.3rem; }}
  .rz-demo-shell {{ align-items:flex-start; flex-direction:column; }}
}}
@media (max-width:480px) {{
  .block-container {{ padding-left:.58rem; padding-right:.58rem; }}
  .rz-page-title {{ font-size:1.34rem; }}
  .rz-page-sub {{ font-size:.84rem; margin-bottom:.9rem; }}
  .rz-login-shell h1 {{ font-size:1.82rem; }}
  .rz-login-proof {{ flex-wrap:wrap; }}
  .stApp:has(.rz-login-shell) [data-testid="stTabs"] {{ padding:.58rem; }}
  [data-testid="stMetric"] {{ min-height:82px; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "Razync Pro • MEI") -> None:
    """Render a consistent, compact page context for every product area."""
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
    grid = "#22384b" if dark else "#d9e7ee"
    axis = "#587084" if dark else "#bfd2de"
    hover_bg = "#0d1824" if dark else "#ffffff"
    hover_text = "#f5f9fc" if dark else "#111c27"
    hover_border = "#365268" if dark else "#cfdee8"
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
