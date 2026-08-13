from __future__ import annotations

import streamlit as st

THEMES = {
    "Claro": {
        "bg": "#f7f9fc",
        "surface": "#ffffff",
        "surface_soft": "#f1f5f9",
        "sidebar": "#ffffff",
        "text": "#111827",
        "muted": "#526071",
        "border": "#d9e2ec",
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "primary_soft": "#e8f1ff",
        "success": "#16a34a",
        "warning": "#d97706",
        "danger": "#dc2626",
        "shadow": "0 8px 28px rgba(15, 23, 42, .06)",
        "shadow_soft": "0 2px 10px rgba(15, 23, 42, .04)",
        "plot": "plotly_white",
    },
    "Escuro": {
        "bg": "#08101f",
        "surface": "#101a2c",
        "surface_soft": "#142137",
        "sidebar": "#0c1627",
        "text": "#f8fafc",
        "muted": "#94a3b8",
        "border": "#26364f",
        "primary": "#3b82f6",
        "primary_hover": "#60a5fa",
        "primary_soft": "#102a56",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "shadow": "0 12px 32px rgba(0, 0, 0, .22)",
        "shadow_soft": "0 4px 16px rgba(0, 0, 0, .16)",
        "plot": "plotly_dark",
    },
}


def tokens(theme_name: str) -> dict:
    return THEMES.get(theme_name, THEMES["Claro"])


def inject_design_system(theme_name: str) -> None:
    t = tokens(theme_name)
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
[data-testid="stSidebar"] {{ background:var(--rz-sidebar, {t['sidebar']}); border-right:1px solid var(--rz-border); }}
[data-testid="stSidebar"] > div:first-child {{ padding-top:.55rem; }}
.block-container {{ max-width:1320px; padding-top:1.25rem; padding-bottom:3rem; }}
h1,h2,h3,h4,p,label,span {{ color:var(--rz-text); }}
small,[data-testid="stCaptionContainer"],.stCaption {{ color:var(--rz-muted)!important; }}

/* Explicit color ownership prevents Streamlit dark defaults leaking into light theme */
[data-testid="stSidebar"] p,[data-testid="stSidebar"] span,[data-testid="stSidebar"] label {{ color:var(--rz-text)!important; }}
[data-testid="stSidebar"] small,[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{ color:var(--rz-muted)!important; }}
[data-testid="stSidebar"] [data-baseweb="base-input"], [data-testid="stSidebar"] [data-baseweb="select"] > div {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; }}
[data-testid="stSidebar"] svg {{ fill:currentColor; color:var(--rz-muted); }}
[data-testid="stAlert"] {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; border-color:var(--rz-border)!important; }}
[data-testid="stAlert"] p {{ color:var(--rz-text)!important; }}
[data-testid="stMarkdownContainer"] a {{ color:var(--rz-primary)!important; }}
[data-testid="stWidgetLabel"] p {{ color:var(--rz-text)!important; }}

/* Brand / shell */
.rz-brand-wrap {{ padding:.55rem .2rem .7rem; }}
.rz-brand {{ font-size:1.48rem; line-height:1; font-weight:900; letter-spacing:-.055em; color:var(--rz-text); }}
.rz-brand span {{ color:var(--rz-primary); }}
.rz-brand-sub {{ margin-top:.38rem; font-size:.77rem; color:var(--rz-muted); }}
.rz-eyebrow {{ color:var(--rz-primary); font-weight:750; font-size:.68rem; text-transform:uppercase; letter-spacing:.11em; margin-bottom:.25rem; }}
.rz-page-title {{ font-size:1.78rem; line-height:1.15; font-weight:820; letter-spacing:-.04em; color:var(--rz-text); }}
.rz-page-sub {{ font-size:.93rem; color:var(--rz-muted); margin-top:.3rem; margin-bottom:1.25rem; max-width:760px; }}
.rz-section-title {{ font-size:1rem; font-weight:760; color:var(--rz-text); margin:.45rem 0 .7rem; }}
.rz-section-sub {{ font-size:.82rem; color:var(--rz-muted); margin-top:-.45rem; margin-bottom:.7rem; }}

/* Business context card */
.rz-business {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:16px; padding:17px 19px; box-shadow:var(--rz-shadow-soft); position:relative; overflow:hidden; }}
.rz-business:before {{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--rz-primary); }}
.rz-business-name {{ font-size:1.05rem; font-weight:780; color:var(--rz-text); }}
.rz-business-meta {{ font-size:.8rem; color:var(--rz-muted); margin-top:4px; }}

/* KPI cards */
[data-testid="stMetric"] {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:15px; padding:16px 17px; box-shadow:var(--rz-shadow-soft); min-height:105px; }}
[data-testid="stMetricLabel"] p {{ color:var(--rz-muted)!important; font-size:.8rem; font-weight:650; }}
[data-testid="stMetricValue"] {{ color:var(--rz-text)!important; font-size:1.48rem; font-weight:800; letter-spacing:-.035em; }}

/* Attention cards */
.rz-alert {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:12px; padding:12px 14px; margin-bottom:8px; box-shadow:var(--rz-shadow-soft); }}
.rz-alert-title {{ font-size:.9rem; font-weight:740; color:var(--rz-text); }}
.rz-alert-text {{ font-size:.8rem; color:var(--rz-muted); margin-top:3px; }}
.rz-alert.rz-danger {{ border-left:3px solid {t['danger']}; }}
.rz-alert.rz-warn {{ border-left:3px solid {t['warning']}; }}
.rz-alert.rz-info {{ border-left:3px solid {t['primary']}; }}
.rz-alert.rz-ok {{ border-left:3px solid {t['success']}; }}

/* Native controls */
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {{
  border-radius:10px; min-height:2.55rem; border:1px solid var(--rz-border); background:var(--rz-surface); color:var(--rz-text); font-weight:660; box-shadow:none;
}}
div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {{ border-color:var(--rz-primary); color:var(--rz-primary); }}
div[data-testid="stFormSubmitButton"] button[kind="primary"], button[kind="primary"] {{ background:var(--rz-primary)!important; color:white!important; border-color:var(--rz-primary)!important; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div, input, textarea {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; border-color:var(--rz-border)!important; border-radius:10px!important; }}
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] li {{ background:var(--rz-surface)!important; color:var(--rz-text)!important; }}
[data-testid="stDataFrame"] {{ border:1px solid var(--rz-border); border-radius:12px; overflow:hidden; background:var(--rz-surface); }}
[data-testid="stExpander"] {{ background:var(--rz-surface); border:1px solid var(--rz-border); border-radius:12px; box-shadow:var(--rz-shadow-soft); }}
[data-testid="stProgressBar"] > div > div {{ background:var(--rz-primary)!important; }}
hr {{ border-color:var(--rz-border); }}

/* Sidebar navigation */

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

/* Responsive behavior */
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


def apply_plot_theme(fig, theme_name: str, *, height: int | None = None) -> None:
    t = tokens(theme_name)
    kwargs = {
        "template": t["plot"],
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": t["text"]},
        "margin": dict(l=0, r=0, t=12, b=0),
        "legend_title_text": "",
    }
    if height:
        kwargs["height"] = height
    fig.update_layout(**kwargs)
