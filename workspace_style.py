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
        @media (max-width: 760px) {
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
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
