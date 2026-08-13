from __future__ import annotations

import streamlit as st

THEMES = {
    "Claro": {
        "bg": "#f6f8fc",
        "surface": "#ffffff",
        "surface_soft": "#eef3f9",
        "sidebar": "#f8faff",
        "text": "#334155",
        "muted": "#718096",
        "border": "#dce5f0",
        "primary": "#4f7fc9",
        "primary_hover": "#3f6fb7",
        "primary_soft": "#eaf2fc",
        "success": "#3f8f69",
        "warning": "#b9853d",
        "danger": "#c65f67",
        "shadow": "0 8px 28px rgba(71, 85, 105, .045)",
        "shadow_soft": "0 2px 10px rgba(71, 85, 105, .035)",
        "plot": "plotly_white",
    },
    "Escuro": {
        "bg": "#0d1422",
        "surface": "#151f31",
        "surface_soft": "#1b2940",
        "sidebar": "#101a2b",
        "text": "#e8eef7",
        "muted": "#9aabc2",
        "border": "#2a3a54",
        "primary": "#6ea2f2",
        "primary_hover": "#8ab5f6",
        "primary_soft": "#1a3152",
        "success": "#5bb98b",
        "warning": "#d7a85a",
        "danger": "#df7b82",
        "shadow": "0 12px 34px rgba(0, 0, 0, .22)",
        "shadow_soft": "0 4px 16px rgba(0, 0, 0, .15)",
        "plot": "plotly_dark",
    },
}


def tokens(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES["Claro"])


def inject_design_system(theme_name: str) -> None:
    t = tokens(theme_name)

    if theme_name == "Claro":
        native_overrides = """
/* Claro: neutraliza superfícies escuras nativas do Streamlit/BaseWeb */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#f6f8fc !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#f8faff !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { color:#718096 !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#ffffff !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#ffffff !important; color:#334155 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#ffffff !important; color:#334155 !important; }
button:not([kind="primary"]) { background:#ffffff !important; color:#475569 !important; border-color:#dce5f0 !important; }
button:not([kind="primary"]):hover { background:#eef3f9 !important; color:#3f6fb7 !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:#eaf2fc !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#eef3f9 !important; }
[data-testid="stFileUploaderDropzone"] { background:#f8faff !important; border-color:#dce5f0 !important; }
[data-testid="stFileUploaderDropzone"] * { color:#526071 !important; }
[data-testid="stTabs"] button { color:#64748b !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#4f7fc9 !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p { color:#475569 !important; }
h1,h2,h3,h4,h5,h6 { color:#334155 !important; }
hr { border-color:#e4ebf3 !important; }
"""
    else:
        native_overrides = """
/* Escuro: neutraliza o tema claro nativo do Streamlit/BaseWeb */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main { background:#0d1422 !important; color:#e8eef7 !important; }
[data-testid="stHeader"] { background:#0d1422 !important; border-bottom:1px solid #202e44 !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#101a2b !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { color:#9aabc2 !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stDataFrame"] { background:#151f31 !important; border-color:#2a3a54 !important; }
[data-testid="stAlert"] { background:#182438 !important; border-color:#2a3a54 !important; }
[data-testid="stAlert"] p, [data-testid="stAlert"] span { color:#dce6f4 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#151f31 !important; color:#e8eef7 !important; border-color:#344861 !important; }
input::placeholder, textarea::placeholder { color:#8192aa !important; opacity:1 !important; }
[data-baseweb="select"] svg, [data-baseweb="input"] svg { color:#9aabc2 !important; fill:#9aabc2 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"] { background:#182438 !important; color:#e8eef7 !important; border-color:#344861 !important; }
[role="option"] { background:#182438 !important; color:#e8eef7 !important; }
[role="option"]:hover, [role="option"][aria-selected="true"] { background:#223654 !important; color:#ffffff !important; }
button:not([kind="primary"]) { background:#172337 !important; color:#dce6f4 !important; border-color:#344861 !important; }
button:not([kind="primary"]):hover { background:#1d3150 !important; color:#8ab5f6 !important; border-color:#5276a5 !important; }
button[kind="primary"] { background:#5e91dd !important; color:#ffffff !important; border-color:#5e91dd !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; color:#cad6e6 !important; border-color:transparent !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:#1a3152 !important; color:#8ab5f6 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#18263b !important; }
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color:#cad6e6 !important; }
[data-testid="stSidebar"] small, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color:#8799b1 !important; }
[data-testid="stFileUploaderDropzone"] { background:#151f31 !important; border-color:#344861 !important; }
[data-testid="stFileUploaderDropzone"] * { color:#aebed2 !important; }
[data-testid="stTabs"] button { color:#9aabc2 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#7faef3 !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p { color:#cbd7e7 !important; }
[data-testid="stCaptionContainer"], .stCaption { color:#90a2b9 !important; }
[data-testid="stMetricLabel"] p { color:#9aabc2 !important; }
[data-testid="stMetricValue"] { color:#edf3fb !important; }
h1,h2,h3,h4,h5,h6 { color:#edf3fb !important; }
hr { border-color:#293950 !important; }
[data-testid="stProgressBar"] > div { background:#223047 !important; }
[data-testid="stDataFrame"] * { border-color:#2a3a54 !important; }
[data-testid="stCheckbox"] label, [data-testid="stRadio"] label { color:#d7e1ef !important; }
[data-testid="stSelectbox"] label, [data-testid="stTextInput"] label, [data-testid="stNumberInput"] label, [data-testid="stDateInput"] label, [data-testid="stTextArea"] label { color:#cbd7e7 !important; }
"""

    dark_overrides = "" if theme_name != "Escuro" else """
/* Dark theme owns all native Streamlit surfaces; no light-base leakage. */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#0c1424 !important; color:#e7edf7 !important; }
[data-testid="stHeader"] { background:#0c1424 !important; border-bottom:1px solid #25344c !important; }
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background:#111c2e !important; border-right-color:#263750 !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { color:#91a3bb !important; }
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stForm"], [data-testid="stAlert"], [data-testid="stDataFrame"] { background:#162238 !important; border-color:#2b3d59 !important; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, [data-baseweb="textarea"] > div, input, textarea { background:#17243a !important; color:#e7edf7 !important; border-color:#334764 !important; box-shadow:none !important; }
[data-baseweb="select"] > div > div, [data-baseweb="input"] > div > div { background:transparent !important; color:#e7edf7 !important; }
[data-baseweb="select"] svg, [data-baseweb="input"] svg { color:#9fb0c6 !important; fill:#9fb0c6 !important; }
[data-baseweb="popover"], [data-baseweb="popover"] > div, [role="listbox"], [role="option"] { background:#17243a !important; color:#e7edf7 !important; border-color:#334764 !important; }
[role="option"]:hover { background:#20314d !important; }
button:not([kind="primary"]) { background:#17243a !important; color:#dce6f3 !important; border-color:#334764 !important; box-shadow:none !important; }
button:not([kind="primary"]):hover { background:#20314d !important; color:#7fb2ff !important; border-color:#4b6f9f !important; }
[data-testid="stSidebar"] button:not([kind="primary"]) { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] button:not([kind="primary"]):hover { background:#1b2c46 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"], [data-testid="stSidebar"] details, [data-testid="stSidebar"] summary { background:transparent !important; border-color:transparent !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover { background:#1b2c46 !important; }
[data-testid="stFileUploaderDropzone"] { background:#142137 !important; border-color:#334764 !important; }
[data-testid="stFileUploaderDropzone"] * { color:#aebed2 !important; }
[data-testid="stTabs"] button { color:#94a7bf !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#79aef8 !important; }
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, [data-testid="stWidgetLabel"] p, label, p, span { color:#d9e3ef !important; }
h1,h2,h3,h4,h5,h6 { color:#f2f6fb !important; }
small,[data-testid="stCaptionContainer"],.stCaption { color:#93a5bc !important; }
[data-testid="stAlert"] { background:#1a2a43 !important; }
[data-testid="stAlert"] p { color:#dce6f3 !important; }
[data-testid="stProgressBar"] > div { background:#23334b !important; }
[data-testid="stProgressBar"] > div > div { background:#4f8ee8 !important; }
[data-testid="stNumberInput"] button { background:#162238 !important; color:#a9bad0 !important; border-color:#334764 !important; }
[data-testid="stNumberInput"] button:hover { background:#20314d !important; }
[data-testid="stRadio"] [role="radiogroup"] label div:first-child { background:#17243a !important; border-color:#50647f !important; }
[data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) div:first-child { background:#4f8ee8 !important; border-color:#7fb2ff !important; }
.rz-current-page { background:#1e3a63 !important; color:#8fc0ff !important; }
.rz-dev { background:#142137 !important; border-color:#2b3d59 !important; color:#8fa2ba !important; }
hr { border-color:#263750 !important; }
"""
    st.markdown(
        f"""
<style>
:root {{
  --rz-bg:{t['bg']}; --rz-surface:{t['surface']}; --rz-soft:{t['surface_soft']};
  --rz-text:{t['text']}; --rz-muted:{t['muted']}; --rz-border:{t['border']};
  --rz-primary:{t['primary']}; --rz-primary-soft:{t['primary_soft']};
  --rz-shadow:{t['shadow']}; --rz-shadow-soft:{t['shadow_soft']};
}}
html, body, [class*="css"] {{ font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
.stApp {{ background:var(--rz-bg); color:var(--rz-text); }}
[data-testid="stHeader"] {{ background:rgba(0,0,0,0); }}
[data-testid="stSidebar"] {{ background:{t['sidebar']}; border-right:1px solid var(--rz-border); }}
[data-testid="stSidebar"] > div:first-child {{ padding-top:.55rem; }}
.block-container {{ max-width:1320px; padding-top:1.25rem; padding-bottom:3rem; }}
h1,h2,h3,h4,p,label,span {{ color:var(--rz-text); }}
small,[data-testid="stCaptionContainer"],.stCaption {{ color:var(--rz-muted)!important; }}
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label {{ color:var(--rz-text)!important; }}
[data-testid="stSidebar"] small,[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:var(--rz-muted)!important; }}
[data-testid="stSidebar"] svg {{ fill:currentColor; color:var(--rz-muted); }}
[data-testid="stAlert"] {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; border-color:var(--rz-border)!important; }}
[data-testid="stAlert"] p {{ color:var(--rz-text)!important; }}
[data-testid="stMarkdownContainer"] a {{ color:var(--rz-primary)!important; }}
[data-testid="stWidgetLabel"] p {{ color:var(--rz-text)!important; }}
.rz-brand-wrap {{ padding:.55rem .2rem .7rem; }}
.rz-brand {{ font-size:1.48rem; line-height:1; font-weight:900; letter-spacing:-.055em; color:var(--rz-text); }}
.rz-brand span {{ color:var(--rz-primary); }}
.rz-brand-sub {{ margin-top:.38rem; font-size:.77rem; color:var(--rz-muted); }}
.rz-eyebrow {{ color:var(--rz-primary); font-weight:750; font-size:.68rem; text-transform:uppercase; letter-spacing:.11em; margin-bottom:.25rem; }}
.rz-page-title {{ font-size:1.78rem; line-height:1.15; font-weight:820; letter-spacing:-.04em; color:var(--rz-text); }}
.rz-page-sub {{ font-size:.93rem; color:var(--rz-muted); margin-top:.3rem; margin-bottom:1.25rem; max-width:760px; }}
.rz-section-title {{ font-size:1rem; font-weight:760; color:var(--rz-text); margin:.45rem 0 .7rem; }}
.rz-section-sub {{ font-size:.82rem; color:var(--rz-muted); margin-top:-.45rem; margin-bottom:.7rem; }}
.rz-business {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:16px; padding:17px 19px; box-shadow:var(--rz-shadow-soft); position:relative; overflow:hidden; }}
.rz-business:before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--rz-primary); }}
.rz-business-name {{ font-size:1.05rem; font-weight:780; color:var(--rz-text); }}
.rz-business-meta {{ font-size:.8rem; color:var(--rz-muted); margin-top:4px; }}
[data-testid="stMetric"] {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:15px; padding:16px 17px; box-shadow:var(--rz-shadow-soft); min-height:105px; }}
[data-testid="stMetricLabel"] p {{ color:var(--rz-muted)!important; font-size:.8rem; font-weight:650; }}
[data-testid="stMetricValue"] {{ color:var(--rz-text)!important; font-size:1.48rem; font-weight:800; letter-spacing:-.035em; }}
.rz-alert {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:12px; padding:12px 14px; margin-bottom:8px; box-shadow:var(--rz-shadow-soft); }}
.rz-alert-title {{ font-size:.9rem; font-weight:740; color:var(--rz-text); }}
.rz-alert-text {{ font-size:.8rem; color:var(--rz-muted); margin-top:3px; }}
.rz-alert.rz-danger {{ border-left:3px solid {t['danger']}; }}
.rz-alert.rz-warn {{ border-left:3px solid {t['warning']}; }}
.rz-alert.rz-info {{ border-left:3px solid {t['primary']}; }}
.rz-alert.rz-ok {{ border-left:3px solid {t['success']}; }}
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{ border-radius:10px; min-height:2.55rem; border:1px solid var(--rz-border); background:var(--rz-surface); color:var(--rz-text); font-weight:660; box-shadow:none; }}
div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {{ border-color:var(--rz-primary); color:var(--rz-primary); }}
div[data-testid="stFormSubmitButton"] button[kind="primary"], button[kind="primary"] {{ background:var(--rz-primary)!important; color:white!important; border-color:var(--rz-primary)!important; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, input, textarea {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; border-color:var(--rz-border)!important; border-radius:10px!important; }}
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] li {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; }}
[data-testid="stDataFrame"] {{ border:1px solid var(--rz-border); border-radius:12px; overflow:hidden; background:var(--rz-surface); }}
[data-testid="stExpander"] {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:12px; box-shadow:var(--rz-shadow-soft); }}
[data-testid="stProgressBar"] > div > div {{ background:var(--rz-primary)!important; }}
hr {{ border-color:var(--rz-border); }}
.rz-sidebar-section {{ font-size:.67rem; font-weight:800; text-transform:uppercase; letter-spacing:.09em; color:var(--rz-muted); margin:.8rem .15rem .32rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] {{ box-shadow:none; border:0; background:transparent; border-radius:10px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] details {{ border:0; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{ border-radius:9px; padding:.32rem .4rem; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {{ background:var(--rz-soft); }}
[data-testid="stSidebar"] [data-testid="stButton"] button {{ width:100%; min-height:2.25rem; text-align:left; justify-content:flex-start; padding:.35rem .65rem; border:0; background:transparent; box-shadow:none; }}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {{ background:var(--rz-primary-soft); color:var(--rz-primary); }}
.rz-current-page {{ background:var(--rz-primary-soft); color:var(--rz-primary); border-radius:9px; padding:.55rem .7rem; font-weight:760; font-size:.86rem; margin-bottom:.3rem; }}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{ padding:.38rem .48rem; border-radius:9px; margin:.08rem 0; transition:.15s ease; }}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ background:var(--rz-soft); }}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {{ background:var(--rz-primary-soft); }}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {{ color:var(--rz-primary)!important; font-weight:720; }}
.rz-nav-label {{ font-size:.68rem; font-weight:760; text-transform:uppercase; letter-spacing:.08em; color:var(--rz-muted); margin:.45rem 0 .15rem; }}
.rz-dev {{ background:var(--rz-soft); border:1px solid var(--rz-border); border-radius:10px; padding:9px 10px; font-size:.72rem; color:var(--rz-muted); margin-top:.65rem; }}
{native_overrides}
@media (max-width: 1000px) {{ .block-container {{ padding-left:1rem; padding-right:1rem; }} [data-testid="stMetric"] {{ min-height:96px; }} }}
@media (max-width: 720px) {{ .rz-page-title {{ font-size:1.5rem; }} .block-container {{ padding-top:.7rem; }} }}
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
    st.markdown(f'<div class="rz-business"><div class="rz-business-name">{name}</div><div class="rz-business-meta">{meta} • visão consolidada financeira e fiscal</div></div>', unsafe_allow_html=True)


def alert_card(level: str, title: str, text: str) -> None:
    cls = {"danger": "rz-danger", "warn": "rz-warn", "info": "rz-info", "ok": "rz-ok"}.get(level, "rz-info")
    st.markdown(f'<div class="rz-alert {cls}"><div class="rz-alert-title">{title}</div><div class="rz-alert-text">{text}</div></div>', unsafe_allow_html=True)



def empty_state(title: str, text: str, icon: str = "○") -> None:
    st.markdown(
        f'<div class="rz-empty"><div class="rz-empty-icon">{icon}</div><div class="rz-empty-title">{title}</div><div class="rz-empty-text">{text}</div></div>',
        unsafe_allow_html=True,
    )


def helper_note(text: str) -> None:
    st.markdown(f'<div class="rz-helper">{text}</div>', unsafe_allow_html=True)

def apply_plot_theme(fig, theme_name: str, *, height: int | None = None) -> None:
    """Apply Razync theme tokens to the entire Plotly figure, including axes and hover UI."""
    t = tokens(theme_name)
    dark = theme_name == "Escuro"
    grid = "#263750" if dark else "#e6edf5"
    axis = "#52657f" if dark else "#cbd6e2"
    hover_bg = "#1b2940" if dark else "#ffffff"
    hover_text = "#edf3fb" if dark else "#334155"
    hover_border = "#3a506f" if dark else "#d9e2ec"
    colorway = [
        t["primary"], t["success"], t["warning"], t["danger"],
        "#9b8cf2" if dark else "#7c6fd1",
        "#5bb7c7" if dark else "#4196a6",
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
        showgrid=False, zeroline=False, linecolor=axis, tickcolor=axis,
        tickfont=dict(color=t["muted"]), title_font=dict(color=t["muted"]),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=grid, gridwidth=1, zeroline=False, linecolor=axis,
        tickcolor=axis, tickfont=dict(color=t["muted"]), title_font=dict(color=t["muted"]),
    )
