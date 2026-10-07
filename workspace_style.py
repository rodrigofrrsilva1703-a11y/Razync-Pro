from __future__ import annotations

import streamlit as st


def inject_workspace_style() -> None:
    """Razync Pro shell V8: editorial workspace, dark rail, open canvas."""
    st.markdown(
        """
<style>
/* =========================================================
   RAZYNC PRO · SHELL V8
   Rebuilt from zero: dark rail + open editorial workspace.
   ========================================================= */

:root {
  --rz-v8-bg: #f5f7f9;
  --rz-v8-paper: #ffffff;
  --rz-v8-text: #111820;
  --rz-v8-muted: #6f7b87;
  --rz-v8-line: #e5e9ed;
  --rz-v8-line-strong: #d7dde3;
  --rz-v8-ink: #07131f;
  --rz-v8-ink-soft: #0d1c2a;
  --rz-v8-accent: #12bce8;
  --rz-v8-accent-soft: #e6f8fd;
  --rz-v8-warn: #a76b12;
  --rz-v8-danger: #b54a55;
}

/* App canvas */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background: var(--rz-v8-bg) !important;
}
[data-testid="stHeader"] {
  background: transparent !important;
  border: 0 !important;
}
.stApp:has(.st-key-sidebar_navigation) [data-testid="stMain"] .block-container {
  max-width: 1180px !important;
  padding: 2.2rem 2.25rem 4rem !important;
}

/* Typography */
.rz-eyebrow {
  margin: 0 0 .55rem !important;
  color: #87929d !important;
  font-size: .64rem !important;
  font-weight: 760 !important;
  letter-spacing: .14em !important;
  text-transform: uppercase;
}
.rz-page-title {
  max-width: 850px;
  color: var(--rz-v8-text) !important;
  font-size: clamp(2rem, 3.5vw, 3rem) !important;
  line-height: .98 !important;
  font-weight: 790 !important;
  letter-spacing: -.055em !important;
}
.rz-page-sub {
  max-width: 650px !important;
  margin: .65rem 0 2.1rem !important;
  color: var(--rz-v8-muted) !important;
  font-size: .92rem !important;
  line-height: 1.62 !important;
}
.rz-section-title {
  margin: 2rem 0 .24rem !important;
  color: var(--rz-v8-text) !important;
  font-size: 1.02rem !important;
  font-weight: 760 !important;
  letter-spacing: -.02em !important;
}
.rz-section-sub {
  margin: 0 0 .85rem !important;
  color: var(--rz-v8-muted) !important;
  font-size: .75rem !important;
  line-height: 1.45 !important;
}

/* Sidebar: real navigation rail */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  width: 258px !important;
  min-width: 258px !important;
  background: var(--rz-v8-ink) !important;
  border-right: 0 !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 1.15rem .9rem 1rem !important;
}
.rz-side-brand {
  display: flex;
  align-items: center;
  gap: .72rem;
  margin: 0 .2rem 1.25rem;
  padding: .1rem .1rem .85rem;
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.rz-side-brand img {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(18,188,232,.35);
  border-radius: 9px;
  object-fit: cover;
  box-shadow: none;
}
.rz-side-brand strong {
  color: #f7fbfd !important;
  font-size: 1rem;
  font-weight: 760;
  letter-spacing: -.03em;
}
.rz-side-brand em {
  margin-left: .24rem;
  color: var(--rz-v8-accent) !important;
  font-size: .55rem;
  font-style: normal;
  font-weight: 850;
  letter-spacing: .11em;
}
.rz-side-brand span {
  display: block;
  max-width: 170px;
  margin-top: .12rem;
  overflow: hidden;
  color: #718396 !important;
  font-size: .65rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.st-key-sidebar_navigation [data-testid="stCaptionContainer"] p {
  margin: .95rem .45rem .28rem !important;
  color: #56697b !important;
  font-size: .58rem !important;
  font-weight: 800 !important;
  letter-spacing: .13em !important;
}
.st-key-sidebar_navigation [data-testid="stButton"] {
  margin: .03rem 0 !important;
}
.st-key-sidebar_navigation [data-testid="stButton"] button {
  min-height: 2.42rem !important;
  justify-content: flex-start !important;
  gap: .62rem !important;
  padding: .38rem .62rem !important;
  border: 0 !important;
  border-radius: 9px !important;
  background: transparent !important;
  color: #91a2b2 !important;
  box-shadow: none !important;
  font-size: .78rem !important;
  font-weight: 620 !important;
}
.st-key-sidebar_navigation [data-testid="stButton"] button:hover {
  background: rgba(255,255,255,.055) !important;
  color: #f7fbfd !important;
}
.st-key-sidebar_navigation [data-testid="stButton"] button:disabled {
  background: rgba(18,188,232,.10) !important;
  color: #e9fbff !important;
  box-shadow: inset 2px 0 0 var(--rz-v8-accent) !important;
  opacity: 1 !important;
}
.st-key-sidebar_navigation [data-testid="stButton"] button p {
  color: inherit !important;
  font-size: inherit !important;
  font-weight: inherit !important;
}
.st-key-sidebar_navigation [data-testid="stExpander"],
[data-testid="stSidebar"] [data-testid="stExpander"] {
  border: 0 !important;
  border-radius: 9px !important;
  background: transparent !important;
  box-shadow: none !important;
}
.st-key-sidebar_navigation [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
  min-height: 2.3rem !important;
  padding: .34rem .55rem !important;
  border-radius: 9px !important;
  color: #8193a3 !important;
  font-size: .74rem !important;
  font-weight: 650 !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
  background: rgba(255,255,255,.05) !important;
}
[data-testid="stSidebar"] hr {
  margin: .85rem 0 !important;
  border-color: rgba(255,255,255,.08) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] input {
  background: var(--rz-v8-ink-soft) !important;
  color: #e8f1f7 !important;
  border-color: rgba(255,255,255,.10) !important;
}

/* KPI strip: no cards */
.rz-stat-card {
  position: relative;
  min-height: 92px;
  padding: .15rem 1.15rem .15rem 0;
  border: 0;
  border-right: 1px solid var(--rz-v8-line);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
[data-testid="column"]:last-child .rz-stat-card {
  border-right: 0;
}
.rz-stat-label {
  display: block;
  margin-bottom: .48rem;
  color: #8a949e !important;
  font-size: .66rem;
  font-weight: 700;
  letter-spacing: .025em;
}
.rz-stat-card strong {
  display: block;
  color: var(--rz-v8-text) !important;
  font-size: clamp(1.42rem, 2.2vw, 1.85rem);
  line-height: 1;
  font-weight: 760;
  letter-spacing: -.05em;
}
.rz-stat-detail {
  display: block;
  margin-top: .42rem;
  color: #98a1aa !important;
  font-size: .64rem;
}
.rz-stat-card.is-danger strong { color: var(--rz-v8-danger) !important; }
.rz-stat-card.is-warning strong { color: var(--rz-v8-warn) !important; }
.rz-stat-card.is-positive strong { color: #147b75 !important; }

/* Open sections: panels are separators, not boxes */
[class*="st-key-rz_panel_"] {
  margin: .2rem 0 1rem;
  padding: 1.15rem 0 1.35rem;
  border: 0;
  border-top: 1px solid var(--rz-v8-line);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
[class*="st-key-rz_panel_"] [data-testid="stCaptionContainer"]:first-child p {
  margin-bottom: .22rem !important;
  color: #8b959f !important;
  font-size: .61rem !important;
  font-weight: 800 !important;
  letter-spacing: .12em !important;
  text-transform: uppercase;
}
[class*="st-key-rz_panel_"] [data-testid="stForm"] {
  padding: .25rem 0 0 !important;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}

/* Forms and controls */
[data-testid="stMain"] [data-testid="stForm"] {
  padding: 0 !important;
  border: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
[data-baseweb="textarea"] > div,
[data-testid="stDateInput"] input,
[data-testid="stNumberInput"] input {
  min-height: 2.7rem !important;
  border: 1px solid var(--rz-v8-line-strong) !important;
  border-radius: 9px !important;
  background: var(--rz-v8-paper) !important;
  color: var(--rz-v8-text) !important;
  box-shadow: 0 1px 0 rgba(13,24,34,.02) !important;
}
[data-baseweb="input"] > div:focus-within,
[data-baseweb="select"] > div:focus-within,
[data-baseweb="textarea"] > div:focus-within {
  border-color: #82dff4 !important;
  box-shadow: 0 0 0 3px rgba(18,188,232,.10) !important;
}
[data-testid="stMain"] label p {
  color: #5f6b76 !important;
  font-size: .72rem !important;
  font-weight: 640 !important;
}

/* Buttons: compact, not giant cards */
[data-testid="stMain"] div[data-testid="stButton"] button,
[data-testid="stMain"] [data-testid="stDownloadButton"] button,
[data-testid="stMain"] [data-testid="stLinkButton"] a {
  min-height: 2.46rem !important;
  padding: .45rem .78rem !important;
  border-radius: 8px !important;
  border: 1px solid var(--rz-v8-line-strong) !important;
  background: var(--rz-v8-paper) !important;
  color: #30404e !important;
  box-shadow: none !important;
  font-size: .76rem !important;
  font-weight: 650 !important;
  transition: border-color .12s ease, background .12s ease, transform .12s ease;
}
[data-testid="stMain"] div[data-testid="stButton"] button:hover,
[data-testid="stMain"] [data-testid="stDownloadButton"] button:hover,
[data-testid="stMain"] [data-testid="stLinkButton"] a:hover {
  transform: translateY(-1px);
  border-color: #9adfeb !important;
  background: #fbfeff !important;
  color: #087b99 !important;
}
[data-testid="stMain"] button[kind="primary"],
[data-testid="stMain"] [data-testid="stLinkButton"] a[kind="primary"] {
  border-color: var(--rz-v8-ink) !important;
  background: var(--rz-v8-ink) !important;
  color: #ffffff !important;
}

/* Expanders become quiet disclosure rows */
[data-testid="stMain"] [data-testid="stExpander"] {
  overflow: hidden;
  border: 0 !important;
  border-top: 1px solid var(--rz-v8-line) !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
[data-testid="stMain"] [data-testid="stExpander"] summary {
  min-height: 3rem !important;
  padding: .58rem .1rem !important;
  color: #52606d !important;
  font-size: .78rem !important;
  font-weight: 660 !important;
}
[data-testid="stMain"] [data-testid="stExpander"] details > div {
  padding-left: .1rem !important;
  padding-right: .1rem !important;
}

/* Tables are the main paper surface */
[data-testid="stMain"] [data-testid="stDataFrame"] {
  overflow: hidden !important;
  border: 1px solid var(--rz-v8-line) !important;
  border-radius: 12px !important;
  background: var(--rz-v8-paper) !important;
  box-shadow: 0 10px 30px rgba(24,39,52,.035) !important;
}

/* Alerts: inline notes */
.rz-alert {
  margin: .75rem 0;
  padding: .72rem .85rem;
  border: 0;
  border-left: 2px solid #9ccbd6;
  border-radius: 0 8px 8px 0;
  background: rgba(255,255,255,.52);
  box-shadow: none;
}
.rz-alert-title {
  color: var(--rz-v8-text) !important;
  font-size: .82rem;
  font-weight: 700;
}
.rz-alert-text {
  margin-top: .18rem;
  color: var(--rz-v8-muted) !important;
  font-size: .74rem;
  line-height: 1.45;
}
.rz-alert.rz-danger { border-left-color: #d86f78; }
.rz-alert.rz-warn { border-left-color: #d8a149; }
.rz-alert.rz-ok { border-left-color: #5ca59d; }

/* Dashboard: one deliberate focal surface */
.rz-dash-intro {
  margin: 0 0 1.45rem;
}
.rz-dash-intro span {
  color: #8b959f !important;
  font-size: .62rem !important;
  font-weight: 780 !important;
  letter-spacing: .14em !important;
}
.rz-dash-intro p {
  max-width: 620px;
  margin: .35rem 0 0 !important;
  color: var(--rz-v8-muted) !important;
  font-size: .84rem !important;
}
.st-key-dashboard_focus {
  position: relative;
  min-height: 220px;
  padding: 1.55rem 1.7rem 1.6rem;
  overflow: hidden;
  border: 0;
  border-radius: 18px;
  background: var(--rz-v8-ink);
  box-shadow: none;
}
.st-key-dashboard_focus::after {
  content: "";
  position: absolute;
  right: -80px;
  bottom: -110px;
  width: 240px;
  height: 240px;
  border: 1px solid rgba(18,188,232,.23);
  border-radius: 999px;
}
.st-key-dashboard_focus [data-testid="stCaptionContainer"] *,
.st-key-dashboard_focus [data-testid="stMarkdownContainer"] p,
.st-key-dashboard_focus [data-testid="stMarkdownContainer"] h3 {
  color: #f6fbfd !important;
  -webkit-text-fill-color: #f6fbfd !important;
}
.st-key-dashboard_focus [data-testid="stMarkdownContainer"] h3 {
  max-width: 620px;
  margin: .5rem 0 .7rem !important;
  font-size: clamp(1.45rem, 2.5vw, 2rem) !important;
  line-height: 1.08 !important;
  letter-spacing: -.04em !important;
}
.st-key-dashboard_focus [data-testid="stButton"] button {
  width: auto !important;
  margin-top: .75rem;
  border-color: var(--rz-v8-accent) !important;
  background: var(--rz-v8-accent) !important;
  color: #05202a !important;
}
.st-key-dashboard_health {
  min-height: 220px;
  padding: 1rem 0 0;
  border: 0;
  border-top: 1px solid var(--rz-v8-line);
  border-radius: 0;
  background: transparent;
}
.rz-health-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .6rem;
  margin-bottom: .72rem;
}
.rz-health-head strong { font-size: .8rem; }
.rz-health-pill {
  padding: .22rem .48rem;
  border: 1px solid var(--rz-v8-line);
  border-radius: 999px;
  color: #74808a !important;
  font-size: .61rem;
  font-weight: 700;
}
.rz-health-row {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: .58rem 0;
  border-top: 1px solid var(--rz-v8-line);
}
.rz-health-row span {
  color: #8a949e !important;
  font-size: .69rem;
}
.rz-health-row strong {
  color: var(--rz-v8-text) !important;
  font-size: .79rem;
}
[class*="st-key-dashboard_task_"],
[class*="st-key-dashboard_deadline_"] {
  margin: 0;
  padding: .72rem 0;
  border: 0;
  border-top: 1px solid var(--rz-v8-line);
  border-radius: 0;
  background: transparent;
}

/* Empty state */
.rz-empty {
  padding: 2.8rem 1.5rem;
  border: 1px dashed var(--rz-v8-line-strong);
  border-radius: 12px;
  background: rgba(255,255,255,.42);
  text-align: center;
}
.rz-empty-icon {
  margin-bottom: .5rem;
  color: #94a0aa !important;
  font-size: 1.15rem;
}
.rz-empty-title {
  color: var(--rz-v8-text) !important;
  font-size: .9rem;
  font-weight: 700;
}
.rz-empty-text {
  max-width: 560px;
  margin: .35rem auto 0;
  color: var(--rz-v8-muted) !important;
  font-size: .76rem;
  line-height: 1.5;
}

/* Helper tags */
.rz-inline-meta {
  display: flex;
  flex-wrap: wrap;
  gap: .35rem;
  margin: .4rem 0 .7rem;
}
.rz-inline-meta span {
  padding: .2rem .42rem;
  border: 0;
  border-radius: 999px;
  background: #e9edf1;
  color: #75818c !important;
  font-size: .61rem;
  font-weight: 650;
}

/* Floating AI */
.st-key-floating_ai_launcher {
  position: fixed !important;
  right: 1rem !important;
  bottom: 1rem !important;
  z-index: 999990 !important;
}
.st-key-floating_ai_launcher [data-testid="stButton"] button {
  min-height: 42px !important;
  padding: .48rem .76rem !important;
  border: 0 !important;
  border-radius: 999px !important;
  background: var(--rz-v8-ink) !important;
  color: #f6fbfd !important;
  box-shadow: 0 12px 26px rgba(4,17,28,.16) !important;
  font-size: .72rem !important;
}

/* Native metrics outside rebuilt areas */
[data-testid="stMain"] [data-testid="stMetric"] {
  min-height: 76px !important;
  padding: .1rem 0 .65rem !important;
  border: 0 !important;
  border-bottom: 1px solid var(--rz-v8-line) !important;
  border-radius: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
}
[data-testid="stMetricLabel"] p {
  color: #89949e !important;
  font-size: .67rem !important;
  font-weight: 680 !important;
}
[data-testid="stMetricValue"] {
  color: var(--rz-v8-text) !important;
  font-size: 1.42rem !important;
  font-weight: 750 !important;
  letter-spacing: -.045em !important;
}

/* Step helper */
.rz-step-grid {
  display: grid;
  grid-template-columns: repeat(3,minmax(0,1fr));
  gap: 0;
  margin: .25rem 0 1.2rem;
  border-top: 1px solid var(--rz-v8-line);
  border-bottom: 1px solid var(--rz-v8-line);
}
.rz-step {
  min-height: 76px;
  padding: .8rem 1rem .78rem 0;
  border: 0;
  border-right: 1px solid var(--rz-v8-line);
  border-radius: 0;
  background: transparent;
}
.rz-step:last-child { border-right: 0; padding-left: 1rem; }
.rz-step:nth-child(2) { padding-left: 1rem; }
.rz-step b {
  display: block;
  margin-bottom: .22rem;
  color: var(--rz-v8-text) !important;
  font-size: .72rem;
}
.rz-step span {
  color: var(--rz-v8-muted) !important;
  font-size: .65rem;
  line-height: 1.4;
}

/* Dark mode keeps same architecture, swaps canvas */
.stApp:has([data-testid="stSidebar"]) [data-theme="dark"] {}
html:has(.stApp) body { overflow-x: hidden; }

/* Mobile */
@media (max-width: 820px) {
  [data-testid="stSidebar"],
  [data-testid="stSidebarContent"] {
    width: min(278px, 88vw) !important;
    min-width: min(278px, 88vw) !important;
  }
  .stApp:has(.st-key-sidebar_navigation) [data-testid="stMain"] .block-container {
    padding: 1.2rem .85rem 4.5rem !important;
  }
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
    gap: .72rem !important;
    flex-wrap: wrap !important;
  }
  [data-testid="stMain"] [data-testid="column"] {
    flex: 1 1 220px !important;
    min-width: 0 !important;
    width: auto !important;
  }
  .rz-page-title { font-size: 2rem !important; }
  .rz-page-sub { margin-bottom: 1.5rem !important; }
  .rz-stat-card {
    min-height: 76px;
    padding: .25rem 0 .8rem;
    border-right: 0;
    border-bottom: 1px solid var(--rz-v8-line);
  }
  .st-key-dashboard_focus {
    min-height: 0;
    padding: 1.25rem;
    border-radius: 14px;
  }
  .st-key-dashboard_health {
    min-height: 0;
  }
  .rz-step-grid {
    grid-template-columns: 1fr;
  }
  .rz-step,
  .rz-step:nth-child(2),
  .rz-step:last-child {
    min-height: 0;
    padding: .65rem 0;
    border-right: 0;
    border-bottom: 1px solid var(--rz-v8-line);
  }
  .rz-step:last-child { border-bottom: 0; }
}
@media (max-width: 520px) {
  [data-testid="stMain"] [data-testid="column"] {
    flex: 1 1 100% !important;
    width: 100% !important;
  }
  .rz-page-title { font-size: 1.85rem !important; }
  [data-testid="stMain"] div[data-testid="stButton"] button,
  [data-testid="stMain"] [data-testid="stDownloadButton"] button {
    min-height: 2.62rem !important;
    white-space: normal !important;
  }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    transition: none !important;
    animation: none !important;
    scroll-behavior: auto !important;
  }
}
</style>
        """,
        unsafe_allow_html=True,
    )
