from __future__ import annotations

import streamlit as st


def inject_workspace_style() -> None:
    st.markdown(
        """
        <style>
        .rz-workspace-note {
            padding: .85rem 1rem;
            border: 1px solid var(--rz-border);
            border-radius: 14px;
            background: var(--rz-soft);
            color: var(--rz-muted);
        }

        [data-testid="stAppViewContainer"] .block-container {
            max-width: 1380px;
        }

        /* Login V3: acesso moderno com marketing original do Razync Pro. */
        .stApp:has(.rz-login-shell) [data-testid="stMain"] {
            min-height: 100vh;
            background:
                radial-gradient(circle at 50% -12%, color-mix(in srgb, var(--rz-primary) 16%, transparent), transparent 34rem),
                linear-gradient(180deg, color-mix(in srgb, var(--rz-bg) 96%, white 4%), var(--rz-bg)) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stMain"]::before,
        .stApp:has(.rz-login-shell) [data-testid="stHeader"] {
            display: none !important;
        }
        .stApp:has(.rz-login-shell) .block-container {
            max-width: 1040px !important;
            padding: clamp(2.2rem, 5vh, 4rem) 1rem 4.5rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-shell {
            max-width: 920px !important;
            margin: 0 auto 1.35rem !important;
            padding: 0 !important;
            text-align: center !important;
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand {
            display: inline-flex !important;
            align-items: center !important;
            gap: .64rem !important;
            margin: 0 auto .95rem !important;
            padding: 0 !important;
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-mark {
            width: 42px !important;
            height: 42px !important;
            border-radius: 12px !important;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 46%, transparent) !important;
            box-shadow: 0 12px 30px color-mix(in srgb, var(--rz-primary) 22%, transparent) !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand strong {
            font-size: 1.38rem !important;
            letter-spacing: -.045em !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand span {
            font-size: .6rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-kicker {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 auto .8rem !important;
            padding: .38rem .7rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 28%, var(--rz-border)) !important;
            border-radius: 999px !important;
            background: color-mix(in srgb, var(--rz-primary) 8%, var(--rz-surface)) !important;
            color: var(--rz-primary) !important;
            font-size: .67rem !important;
            font-weight: 780 !important;
            letter-spacing: .04em !important;
            text-transform: uppercase !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-shell h1 {
            display: block !important;
            max-width: 780px !important;
            margin: 0 auto !important;
            font-size: clamp(2.15rem, 5vw, 3.35rem) !important;
            line-height: 1.02 !important;
            letter-spacing: -.055em !important;
            font-weight: 870 !important;
            color: var(--rz-text) !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-shell h1 em {
            color: var(--rz-primary) !important;
            font-style: normal !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-lead {
            display: block !important;
            max-width: 690px !important;
            margin: .9rem auto 1.35rem !important;
            color: var(--rz-muted) !important;
            font-size: .98rem !important;
            line-height: 1.65 !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits {
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: .72rem !important;
            max-width: 820px !important;
            margin: 0 auto 1rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits span {
            display: flex !important;
            align-items: center !important;
            gap: .62rem !important;
            min-height: 72px !important;
            padding: .82rem .9rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-border) 88%, transparent) !important;
            border-radius: 16px !important;
            background: color-mix(in srgb, var(--rz-surface) 96%, transparent) !important;
            color: var(--rz-text) !important;
            box-shadow: 0 12px 35px rgba(18, 31, 43, .055) !important;
            text-align: left !important;
            font-size: .82rem !important;
            font-weight: 720 !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits b {
            display: inline-grid !important;
            place-items: center !important;
            flex: 0 0 30px !important;
            width: 30px !important;
            height: 30px !important;
            border-radius: 9px !important;
            background: color-mix(in srgb, var(--rz-primary) 12%, var(--rz-surface)) !important;
            color: var(--rz-primary) !important;
            font-size: .66rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-proof {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: .7rem !important;
            margin: .2rem auto .7rem !important;
            color: var(--rz-muted) !important;
            font-size: .7rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-proof span {
            color: var(--rz-muted) !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-proof i {
            width: 4px !important;
            height: 4px !important;
            border-radius: 50% !important;
            background: var(--rz-primary) !important;
        }

        .stApp:has(.rz-login-shell) > div [data-testid="stCaptionContainer"] {
            color: var(--rz-muted) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] {
            max-width: 460px !important;
            margin: 1.15rem auto 0 !important;
            padding: 1rem 1.05rem 1.15rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-border) 92%, transparent) !important;
            border-radius: 22px !important;
            background: color-mix(in srgb, var(--rz-surface) 98%, transparent) !important;
            box-shadow: 0 28px 80px rgba(18, 31, 43, .11), 0 3px 12px rgba(18, 31, 43, .04) !important;
            backdrop-filter: blur(20px) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tablist"] {
            gap: .15rem !important;
            margin-bottom: .35rem !important;
            padding: .22rem !important;
            border: 0 !important;
            border-radius: 12px !important;
            background: var(--rz-soft) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] {
            min-height: 2.35rem !important;
            border-radius: 9px !important;
            font-size: .76rem !important;
            font-weight: 690 !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            background: var(--rz-surface) !important;
            color: var(--rz-text) !important;
            box-shadow: 0 2px 8px rgba(16, 28, 40, .08) !important;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading {
            padding: .75rem .05rem .35rem !important;
            text-align: left !important;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading strong {
            font-size: 1.35rem !important;
            letter-spacing: -.035em !important;
            font-weight: 820 !important;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading span {
            font-size: .78rem !important;
            line-height: 1.45 !important;
            color: var(--rz-muted) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [data-testid="stForm"] {
            padding: .45rem 0 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTextInput"] label p {
            font-size: .74rem !important;
            font-weight: 700 !important;
        }
        .stApp:has(.rz-login-shell) [data-baseweb="input"] {
            min-height: 3rem !important;
            border: 1px solid var(--rz-control-border) !important;
            border-radius: 12px !important;
            background: var(--rz-control-bg) !important;
            box-shadow: 0 1px 2px rgba(16, 28, 40, .03) !important;
        }
        .stApp:has(.rz-login-shell) [data-baseweb="input"]:focus-within {
            border-color: var(--rz-primary) !important;
            box-shadow: 0 0 0 4px color-mix(in srgb, var(--rz-primary) 12%, transparent) !important;
        }
        .stApp:has(.rz-login-shell) input {
            min-height: 3rem !important;
            padding-left: .88rem !important;
            font-size: .9rem !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button {
            min-height: 3rem !important;
            margin-top: .3rem !important;
            border: 0 !important;
            border-radius: 12px !important;
            background: var(--rz-primary) !important;
            color: #fff !important;
            font-weight: 790 !important;
            box-shadow: 0 10px 24px color-mix(in srgb, var(--rz-primary) 23%, transparent) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stLinkButton"] a {
            min-height: 2.8rem !important;
            border-radius: 12px !important;
            border: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            color: var(--rz-text) !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stButton"] {
            max-width: 460px !important;
            margin: .8rem auto 0 !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stButton"] button {
            min-height: 2.55rem !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 999px !important;
            background: color-mix(in srgb, var(--rz-surface) 94%, transparent) !important;
            color: var(--rz-muted) !important;
            box-shadow: none !important;
            font-size: .76rem !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stExpander"] {
            max-width: 460px !important;
            margin: .65rem auto 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stExpander"] summary {
            justify-content: center !important;
            color: var(--rz-muted) !important;
            font-size: .7rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-security {
            max-width: 460px !important;
            margin: .4rem auto 0 !important;
            text-align: center !important;
            font-size: .62rem !important;
            color: var(--rz-muted) !important;
            opacity: .88;
        }

        @media (max-width: 980px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding-left: 1.15rem;
                padding-right: 1.15rem;
            }
            .stApp:has(.rz-login-shell) .block-container {
                max-width: 760px !important;
            }
        }

        @media (max-width: 760px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding-top: 1rem;
                padding-left: .82rem;
                padding-right: .82rem;
            }
            [data-testid="stHorizontalBlock"] {
                gap: .55rem !important;
            }
            [data-testid="stMetric"] {
                padding: .72rem .78rem;
                border: 1px solid var(--rz-border);
                border-radius: 12px;
                background: var(--rz-surface);
            }
            [data-testid="stMetricValue"] {
                font-size: 1.32rem;
            }
            [data-testid="stButton"] button,
            [data-testid="stLinkButton"] a {
                min-height: 2.72rem;
            }
            [data-testid="stDataFrame"] {
                border-radius: 12px;
                overflow: hidden;
            }
            [data-testid="stExpander"] summary {
                min-height: 2.6rem;
            }
            [data-testid="stForm"] {
                border-radius: 14px;
            }
            h1 {
                font-size: 1.72rem !important;
                line-height: 1.15 !important;
            }
            h2 {
                font-size: 1.35rem !important;
            }
            h3 {
                font-size: 1.08rem !important;
            }
            .stApp:has(.rz-login-shell) .block-container {
                padding: 1.35rem .75rem 3rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-shell h1 {
                font-size: 2.25rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-benefits {
                grid-template-columns: 1fr !important;
                max-width: 460px !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-benefits span {
                min-height: 60px !important;
            }
            .stApp:has(.rz-login-shell) [data-testid="stTabs"] {
                border-radius: 18px !important;
                padding: .85rem .78rem 1rem !important;
            }
        }

        @media (max-width: 480px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding-left: .62rem;
                padding-right: .62rem;
            }
            [data-testid="stHorizontalBlock"] {
                gap: .42rem !important;
            }
            [data-testid="stButton"] button,
            [data-testid="stLinkButton"] a,
            [data-testid="stDownloadButton"] button {
                min-height: 2.9rem;
                white-space: normal;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.16rem;
            }
            [data-testid="stMetricLabel"] {
                font-size: .76rem;
            }
            [data-testid="stForm"] {
                padding: .78rem;
            }
            [data-testid="stFileUploader"] section {
                min-height: 5.2rem;
            }
            h1 {
                font-size: 1.52rem !important;
            }
            h2 {
                font-size: 1.22rem !important;
            }
            .stApp:has(.rz-login-shell) .block-container {
                padding-left: .55rem !important;
                padding-right: .55rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-shell h1 {
                font-size: 1.9rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-lead {
                font-size: .88rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-proof {
                flex-wrap: wrap !important;
            }
            .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] p {
                font-size: .68rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-auth-heading strong {
                font-size: 1.2rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )