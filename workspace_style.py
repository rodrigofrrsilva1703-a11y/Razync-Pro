from __future__ import annotations

import streamlit as st


def inject_workspace_style() -> None:
    """Razync Pro workspace skin: one coherent SaaS visual layer for desktop and mobile."""
    st.markdown(
        """
        <style>
        /* =========================================================
           RAZYNC PRO · WORKSPACE V6
           Modern, quiet, high-contrast SaaS UI with low visual noise.
           ========================================================= */

        .stApp:has(.st-key-sidebar_navigation) [data-testid="stMain"] {
            background:
                radial-gradient(circle at 78% -12%, color-mix(in srgb, var(--rz-primary) 7%, transparent), transparent 28rem),
                var(--rz-bg);
        }
        .stApp:has(.st-key-sidebar_navigation) [data-testid="stMain"] .block-container {
            max-width: 1280px !important;
            padding: 1.55rem 1.55rem 3.2rem !important;
        }

        @keyframes rz-rise {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .rz-page-title,
        [class*="st-key-rz_panel_"],
        [class*="st-key-rz_metric_card_"] {
            animation: rz-rise .22s ease-out both;
        }

        /* Page rhythm */
        .rz-eyebrow {
            margin-bottom: .28rem !important;
            color: var(--rz-primary) !important;
            font-size: .66rem !important;
            font-weight: 820 !important;
            letter-spacing: .115em !important;
        }
        .rz-page-title {
            font-size: clamp(1.72rem, 2.35vw, 2.28rem) !important;
            font-weight: 820 !important;
            line-height: 1.07 !important;
            letter-spacing: -.048em !important;
        }
        .rz-page-sub {
            max-width: 760px !important;
            margin: .38rem 0 1.35rem !important;
            color: var(--rz-muted) !important;
            font-size: .88rem !important;
            line-height: 1.55 !important;
        }
        .rz-section-title {
            margin: .72rem 0 .26rem !important;
            font-size: .98rem !important;
            font-weight: 780 !important;
            letter-spacing: -.015em !important;
        }
        .rz-section-sub {
            margin: 0 0 .72rem !important;
            color: var(--rz-muted) !important;
            font-size: .76rem !important;
        }

        /* Business identity bar */
        .rz-business {
            position: relative;
            overflow: hidden;
            margin-bottom: 1rem;
            padding: .85rem 1rem .85rem 1.15rem !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 14px !important;
            background: color-mix(in srgb, var(--rz-surface) 97%, var(--rz-primary) 3%) !important;
            box-shadow: none !important;
        }
        .rz-business::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 3px;
            background: linear-gradient(180deg, var(--rz-primary), color-mix(in srgb, var(--rz-primary) 25%, transparent));
        }

        /* Native surfaces */
        [data-testid="stMain"] [data-testid="stMetric"],
        [data-testid="stMain"] [data-testid="stForm"],
        [data-testid="stMain"] [data-testid="stExpander"],
        [data-testid="stMain"] [data-testid="stDataFrame"],
        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stMetric"] {
            min-height: 84px !important;
            padding: .78rem .9rem !important;
            border-radius: 14px !important;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--rz-muted) !important;
            font-size: .73rem !important;
            font-weight: 670 !important;
        }
        [data-testid="stMetricValue"] {
            color: var(--rz-text) !important;
            font-size: 1.32rem !important;
            font-weight: 800 !important;
            letter-spacing: -.035em !important;
        }
        [data-testid="stMain"] [data-testid="stForm"] {
            padding: .92rem !important;
            border-radius: 14px !important;
        }
        [data-testid="stMain"] [data-testid="stExpander"] {
            overflow: hidden;
            border-radius: 13px !important;
        }
        [data-testid="stMain"] [data-testid="stExpander"] summary {
            min-height: 2.7rem !important;
            padding: .5rem .75rem !important;
            font-size: .82rem !important;
            font-weight: 690 !important;
        }
        [data-testid="stMain"] [data-testid="stDataFrame"] {
            overflow: hidden !important;
            border-radius: 13px !important;
        }
        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
        }
        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: .9rem !important;
        }

        /* Controls */
        [data-testid="stMain"] div[data-testid="stButton"] button,
        [data-testid="stMain"] [data-testid="stDownloadButton"] button,
        [data-testid="stMain"] [data-testid="stLinkButton"] a {
            min-height: 2.55rem;
            border-radius: 10px !important;
            font-size: .8rem !important;
            font-weight: 690 !important;
            transition: transform .14s ease, border-color .14s ease, background .14s ease !important;
        }
        [data-testid="stMain"] div[data-testid="stButton"] button:hover,
        [data-testid="stMain"] [data-testid="stDownloadButton"] button:hover,
        [data-testid="stMain"] [data-testid="stLinkButton"] a:hover {
            transform: translateY(-1px);
        }
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] > div {
            min-height: 2.62rem !important;
            border-radius: 10px !important;
        }
        [data-testid="stMain"] [data-testid="stTabs"] [role="tablist"] {
            gap: .2rem !important;
            margin-bottom: .7rem !important;
            padding: .18rem !important;
            border-radius: 11px !important;
            background: color-mix(in srgb, var(--rz-soft) 78%, transparent) !important;
        }
        [data-testid="stMain"] [data-testid="stTabs"] [role="tab"] {
            min-height: 2.35rem !important;
            padding: .35rem .7rem !important;
            border-radius: 9px !important;
            font-size: .76rem !important;
            font-weight: 680 !important;
        }
        [data-testid="stMain"] [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            background: var(--rz-surface) !important;
            box-shadow: var(--rz-shadow-soft) !important;
        }

        /* Compact cards */
        [class*="st-key-rz_metric_card_"] button {
            min-height: 92px !important;
            padding: .92rem 1rem !important;
            justify-content: flex-start !important;
            text-align: left !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 15px !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
        }
        [class*="st-key-rz_metric_card_"] button:hover {
            border-color: color-mix(in srgb, var(--rz-primary) 65%, var(--rz-border)) !important;
            background: color-mix(in srgb, var(--rz-primary-soft) 55%, var(--rz-surface)) !important;
        }
        [class*="st-key-rz_metric_card_"] button p {
            width: 100% !important;
            text-align: left !important;
            white-space: normal !important;
            color: var(--rz-muted) !important;
            font-size: .73rem !important;
            line-height: 1.25 !important;
        }
        [class*="st-key-rz_metric_card_"] button p strong {
            display: block;
            margin-top: .32rem;
            color: var(--rz-text) !important;
            font-size: clamp(1.12rem, 1.7vw, 1.48rem) !important;
            font-weight: 820 !important;
            letter-spacing: -.035em !important;
        }
        [class*="st-key-rz_nav_card_"] button,
        [class*="st-key-rz_quick_card_"] button,
        [class*="st-key-rz_action_card_"] button {
            min-height: 56px !important;
            justify-content: flex-start !important;
            padding: .7rem .85rem !important;
            text-align: left !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 12px !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
        }
        [class*="st-key-rz_nav_card_"] button:hover,
        [class*="st-key-rz_quick_card_"] button:hover,
        [class*="st-key-rz_action_card_"] button:hover {
            border-color: var(--rz-primary) !important;
            background: var(--rz-primary-soft) !important;
        }


        /* Reusable tool panels */
        [class*="st-key-rz_panel_"] {
            padding: 1rem 1.05rem;
            border: 1px solid var(--rz-border);
            border-radius: 15px;
            background: var(--rz-surface);
            box-shadow: none;
        }
        [class*="st-key-rz_panel_"] [data-testid="stCaptionContainer"]:first-child p {
            margin-bottom: .15rem !important;
            color: var(--rz-primary) !important;
            font-size: .64rem !important;
            font-weight: 820 !important;
            letter-spacing: .09em !important;
            text-transform: uppercase;
        }
        .rz-step-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .6rem;
            margin: .25rem 0 .9rem;
        }
        .rz-step {
            min-height: 74px;
            padding: .72rem .78rem;
            border: 1px solid var(--rz-border);
            border-radius: 12px;
            background: color-mix(in srgb, var(--rz-surface) 96%, var(--rz-primary) 4%);
        }
        .rz-step b {
            display: block;
            margin-bottom: .18rem;
            color: var(--rz-text) !important;
            font-size: .76rem;
        }
        .rz-step span {
            color: var(--rz-muted) !important;
            font-size: .69rem;
            line-height: 1.35;
        }
        .rz-inline-meta {
            display: flex;
            flex-wrap: wrap;
            gap: .42rem;
            margin: .15rem 0 .8rem;
        }
        .rz-inline-meta span {
            padding: .28rem .52rem;
            border: 1px solid var(--rz-border);
            border-radius: 999px;
            background: var(--rz-soft);
            color: var(--rz-muted) !important;
            font-size: .66rem;
            font-weight: 690;
        }

        /* Dashboard hero */
        .rz-dash-intro {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 1rem;
            margin: .05rem 0 .85rem;
        }
        .rz-dash-intro span {
            color: var(--rz-primary) !important;
            font-size: .66rem !important;
            font-weight: 830 !important;
            letter-spacing: .115em !important;
        }
        .rz-dash-intro p {
            margin: .25rem 0 0 !important;
            color: var(--rz-muted) !important;
            font-size: .84rem !important;
        }
        .st-key-dashboard_focus {
            position: relative;
            min-height: 218px;
            overflow: hidden;
            padding: 1.3rem 1.4rem 1.35rem;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 38%, var(--rz-border));
            border-radius: 18px;
            background:
                radial-gradient(circle at 88% 12%, rgba(77, 211, 255, .18), transparent 14rem),
                linear-gradient(135deg, #081621 0%, #0d2939 100%);
            box-shadow: 0 18px 45px rgba(3, 18, 28, .16);
        }
        .st-key-dashboard_focus::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: var(--rz-primary);
        }
        .st-key-dashboard_focus [data-testid="stCaptionContainer"] *,
        .st-key-dashboard_focus [data-testid="stMarkdownContainer"] p,
        .st-key-dashboard_focus [data-testid="stMarkdownContainer"] h3 {
            color: #f7fbfe !important;
            -webkit-text-fill-color: #f7fbfe !important;
        }
        .st-key-dashboard_focus [data-testid="stMarkdownContainer"] h3 {
            margin: .35rem 0 .58rem !important;
            font-size: clamp(1.35rem, 2.2vw, 1.82rem) !important;
            line-height: 1.16 !important;
            letter-spacing: -.035em !important;
        }
        .st-key-dashboard_focus [data-testid="stButton"] button {
            margin-top: .55rem;
            border-color: var(--rz-primary) !important;
            background: var(--rz-primary) !important;
            color: #04121a !important;
            font-weight: 780 !important;
        }
        .st-key-dashboard_health {
            min-height: 218px;
            padding: 1.2rem 1.25rem;
            border: 1px solid var(--rz-border);
            border-radius: 18px;
            background: var(--rz-surface);
        }
        .rz-health-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: .75rem;
            margin-bottom: .8rem;
        }
        .rz-health-head strong {
            font-size: .83rem;
        }
        .rz-health-pill {
            display: inline-flex;
            align-items: center;
            min-height: 26px;
            padding: .22rem .55rem;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 28%, var(--rz-border));
            border-radius: 999px;
            background: var(--rz-primary-soft);
            color: var(--rz-primary) !important;
            font-size: .66rem;
            font-weight: 780;
        }
        .rz-health-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: .58rem 0;
            border-top: 1px solid var(--rz-border);
        }
        .rz-health-row span {
            color: var(--rz-muted) !important;
            font-size: .73rem;
        }
        .rz-health-row strong {
            color: var(--rz-text) !important;
            font-size: .82rem;
        }
        [class*="st-key-dashboard_task_"],
        [class*="st-key-dashboard_deadline_"] {
            margin-bottom: .58rem;
            padding: .78rem .85rem;
            border: 1px solid var(--rz-border);
            border-radius: 12px;
            background: var(--rz-surface);
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            border-right: 1px solid var(--rz-border) !important;
            background: color-mix(in srgb, var(--rz-surface) 96%, var(--rz-bg)) !important;
        }
        [data-testid="stSidebar"] .block-container {
            padding: .9rem .78rem 1rem !important;
        }
        .rz-side-brand {
            display: flex;
            align-items: center;
            gap: .68rem;
            padding: .16rem .34rem .72rem;
            margin-bottom: .12rem;
        }
        .rz-side-brand img {
            width: 36px;
            height: 36px;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 26%, var(--rz-border));
            border-radius: 11px;
            object-fit: cover;
            box-shadow: 0 8px 22px color-mix(in srgb, var(--rz-primary) 12%, transparent);
        }
        .rz-side-brand strong {
            color: var(--rz-text) !important;
            font-size: 1.02rem;
            letter-spacing: -.03em;
        }
        .rz-side-brand em {
            margin-left: .24rem;
            color: var(--rz-primary) !important;
            font-size: .56rem;
            font-style: normal;
            font-weight: 850;
            letter-spacing: .09em;
            vertical-align: .12rem;
        }
        .rz-side-brand span {
            display: block;
            max-width: 176px;
            margin-top: .08rem;
            overflow: hidden;
            color: var(--rz-muted) !important;
            font-size: .67rem;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .st-key-sidebar_navigation [data-testid="stCaptionContainer"] p {
            margin: .72rem .35rem .16rem !important;
            color: var(--rz-muted) !important;
            font-size: .61rem !important;
            font-weight: 820 !important;
            letter-spacing: .105em !important;
        }
        .st-key-sidebar_navigation [data-testid="stButton"] {
            margin: .03rem 0 !important;
        }
        .st-key-sidebar_navigation [data-testid="stButton"] button {
            min-height: 2.42rem !important;
            justify-content: flex-start !important;
            gap: .62rem !important;
            padding: .38rem .58rem !important;
            border: 0 !important;
            border-radius: 10px !important;
            background: transparent !important;
            color: var(--rz-muted) !important;
            box-shadow: none !important;
        }
        .st-key-sidebar_navigation [data-testid="stButton"] button:hover {
            background: var(--rz-soft) !important;
            color: var(--rz-text) !important;
        }
        .st-key-sidebar_navigation [data-testid="stButton"] button:disabled {
            background: var(--rz-primary-soft) !important;
            color: var(--rz-primary) !important;
            font-weight: 750 !important;
            opacity: 1 !important;
        }
        .st-key-sidebar_navigation [data-testid="stButton"] button p {
            font-size: .8rem !important;
            font-weight: 620 !important;
        }
        .st-key-sidebar_navigation [data-testid="stExpander"] {
            border: 0 !important;
            background: transparent !important;
        }
        .st-key-sidebar_navigation [data-testid="stExpander"] summary {
            min-height: 2.35rem !important;
            padding: .32rem .48rem !important;
            border-radius: 10px !important;
            color: var(--rz-muted) !important;
            font-size: .78rem !important;
            font-weight: 690 !important;
        }
        .st-key-sidebar_navigation [data-testid="stExpander"] details > div {
            padding-left: .22rem !important;
            border-left: 1px solid var(--rz-border);
        }
        [data-testid="stSidebar"] hr {
            margin: .7rem 0 !important;
        }

        /* Floating AI */
        .st-key-floating_ai_launcher {
            position: fixed !important;
            right: 1rem !important;
            bottom: 1rem !important;
            z-index: 999990 !important;
            width: auto !important;
        }
        .st-key-floating_ai_launcher [data-testid="stButton"] button {
            min-height: 44px !important;
            padding: .52rem .88rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 55%, transparent) !important;
            border-radius: 999px !important;
            background: linear-gradient(135deg, #087ea4, #0aaee0) !important;
            color: #fff !important;
            box-shadow: 0 12px 30px rgba(2, 49, 69, .22) !important;
            font-size: .76rem !important;
            font-weight: 760 !important;
        }

        /* Mobile */
        @media (max-width: 820px) {
            .stApp:has(.st-key-sidebar_navigation) [data-testid="stMain"] .block-container {
                padding: .95rem .75rem 4.5rem !important;
            }
            [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
                gap: .55rem !important;
                flex-wrap: wrap !important;
            }
            [data-testid="stMain"] [data-testid="column"] {
                flex: 1 1 210px !important;
                min-width: 0 !important;
                width: auto !important;
            }
            [data-testid="stSidebar"] {
                width: min(300px, 88vw) !important;
                min-width: min(300px, 88vw) !important;
            }
            .rz-page-title {
                font-size: 1.62rem !important;
            }
            .rz-page-sub {
                margin-bottom: 1rem !important;
                font-size: .82rem !important;
            }
            .st-key-dashboard_focus,
            .st-key-dashboard_health {
                min-height: 0;
                padding: 1rem;
                border-radius: 15px;
            }
            [class*="st-key-rz_metric_card_"] button {
                min-height: 76px !important;
                padding: .75rem .82rem !important;
            }
            [data-testid="stMain"] [data-testid="stForm"] {
                padding: .75rem !important;
            }
            [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
                min-height: 5rem !important;
                padding: .7rem !important;
            }
            [class*="st-key-rz_panel_"] {
                padding: .78rem .8rem;
                border-radius: 13px;
            }
            .rz-step-grid {
                grid-template-columns: 1fr;
                gap: .42rem;
            }
            .rz-step {
                min-height: 0;
                padding: .6rem .68rem;
            }
            .st-key-floating_ai_launcher {
                right: .65rem !important;
                bottom: .65rem !important;
            }
        }

        @media (max-width: 520px) {
            .stApp:has(.st-key-sidebar_navigation) [data-testid="stMain"] .block-container {
                padding-left: .58rem !important;
                padding-right: .58rem !important;
            }
            [data-testid="stMain"] [data-testid="stHorizontalBlock"] {
                gap: .42rem !important;
            }
            [data-testid="stMain"] [data-testid="column"] {
                flex: 1 1 100% !important;
                width: 100% !important;
            }
            [data-testid="stMain"] div[data-testid="stButton"] button,
            [data-testid="stMain"] [data-testid="stDownloadButton"] button {
                min-height: 2.72rem !important;
                white-space: normal !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.16rem !important;
            }
            .rz-side-brand span {
                max-width: 150px;
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
