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

        .rz-sidebar-label {
            margin: .2rem .7rem .35rem;
            color: var(--rz-muted);
            font-size: .64rem;
            font-weight: 800;
            letter-spacing: .1em;
        }

        .st-key-mobile_bottom_nav {
            display: none;
        }

        [data-testid="stAppViewContainer"] .block-container {
            max-width: 1380px;
        }

        @media (max-width: 980px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding-left: 1.15rem;
                padding-right: 1.15rem;
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
            .st-key-mobile_bottom_nav {
                position: fixed !important;
                z-index: 999980 !important;
                right: .45rem !important;
                bottom: .42rem !important;
                left: .45rem !important;
                display: block !important;
                padding: .34rem !important;
                border: 1px solid var(--rz-border) !important;
                border-radius: 16px !important;
                background: color-mix(in srgb, var(--rz-surface) 94%, transparent) !important;
                box-shadow: 0 14px 40px rgba(2, 23, 34, .2) !important;
                backdrop-filter: blur(16px);
            }
            .st-key-mobile_bottom_nav > div,
            .st-key-mobile_bottom_nav [data-testid="stHorizontalBlock"] {
                gap: .22rem !important;
            }
            .st-key-mobile_bottom_nav [data-testid="column"] {
                min-width: 0 !important;
                flex: 1 1 0 !important;
            }
            .st-key-mobile_bottom_nav [data-testid="stButton"] button {
                min-height: 3.18rem !important;
                gap: .08rem !important;
                flex-direction: column !important;
                justify-content: center !important;
                padding: .22rem .12rem !important;
                border: 0 !important;
                border-radius: 11px !important;
                background: transparent !important;
                box-shadow: none !important;
            }
            .st-key-mobile_bottom_nav [data-testid="stButton"] button:disabled {
                color: var(--rz-primary) !important;
                background: var(--rz-primary-soft) !important;
                opacity: 1 !important;
            }
            .st-key-mobile_bottom_nav [data-testid="stButton"] button p {
                font-size: .61rem !important;
                line-height: 1.05 !important;
                white-space: nowrap !important;
            }
            .st-key-mobile_bottom_nav [data-testid="stButton"] button span {
                font-size: 1.12rem !important;
            }
            .st-key-floating_ai_launcher {
                display: none !important;
            }
            .st-key-floating_ai_v7_shell {
                bottom: 4.35rem !important;
                max-height: calc(100vh - 5rem) !important;
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
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

