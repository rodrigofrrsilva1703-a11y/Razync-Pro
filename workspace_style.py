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