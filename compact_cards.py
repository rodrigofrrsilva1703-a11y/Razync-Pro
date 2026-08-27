from __future__ import annotations

import streamlit as st


def inject_compact_cards() -> None:
    """Apply a denser card rhythm to product workspaces without touching auth screens."""
    st.markdown(
        """
        <style>
        [data-testid="stMetric"] {
            min-height: 84px !important;
            padding: 11px 13px !important;
            border-radius: 11px !important;
        }
        [data-testid="stMetricLabel"] p {
            font-size: .74rem !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.3rem !important;
            line-height: 1.12 !important;
        }

        [class*="st-key-rz_action_card_"] button,
        [class*="st-key-rz_quick_card_"] button {
            min-height: 58px !important;
            padding: 10px 13px !important;
            border-radius: 11px !important;
        }
        [class*="st-key-rz_action_card_"] button p,
        [class*="st-key-rz_quick_card_"] button p {
            line-height: 1.28 !important;
            font-size: .79rem !important;
        }

        [class*="st-key-rz_metric_card_"] button {
            min-height: 58px !important;
            height: auto !important;
            padding: 10px 13px !important;
            justify-content: flex-start !important;
            text-align: left !important;
            border-radius: 11px !important;
            border: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
            transition: transform .16s ease, border-color .16s ease, background .16s ease !important;
        }
        [class*="st-key-rz_metric_card_"] button:hover {
            transform: translateY(-1px) !important;
            border-color: var(--rz-primary) !important;
            background: var(--rz-primary-soft) !important;
            box-shadow: none !important;
        }
        [class*="st-key-rz_metric_card_"] button p {
            width: 100% !important;
            text-align: left !important;
            white-space: normal !important;
            line-height: 1.22 !important;
            font-size: .76rem !important;
        }
        [class*="st-key-rz_nav_card_"] button {
            min-height: 52px !important;
            justify-content: flex-start !important;
            padding: 9px 12px !important;
            text-align: left !important;
            border-radius: 10px !important;
            border: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
        }
        [class*="st-key-rz_nav_card_"] button:hover {
            color: var(--rz-primary) !important;
            border-color: var(--rz-primary) !important;
            background: var(--rz-primary-soft) !important;
        }
        [class*="st-key-rz_nav_card_"] button p {
            width: 100% !important;
            text-align: left !important;
            font-size: .8rem !important;
        }
        .rz-alert {
            padding: 9px 12px !important;
            margin-bottom: 6px !important;
        }
        .rz-alert-title { font-size: .84rem !important; }
        .rz-alert-text { font-size: .75rem !important; }
        .rz-business { padding: 12px 14px !important; border-radius: 11px !important; }
        .rz-business-name { font-size: .96rem !important; }
        .rz-business-meta { font-size: .74rem !important; }
        .rz-empty { padding: 20px 16px !important; }
        .rz-helper { padding: 8px 10px !important; }

        /* Densidade compartilhada por todas as ferramentas autenticadas. */
        [data-testid="stMain"] .block-container {
            max-width: 1240px !important;
            padding-top: 1rem !important;
            padding-bottom: 2.2rem !important;
        }
        [data-testid="stMain"] [data-testid="stForm"] {
            padding: .8rem !important;
            border-radius: 11px !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stExpander"] {
            border-radius: 10px !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stExpander"] summary {
            min-height: 2.45rem !important;
            padding: .45rem .7rem !important;
        }
        [data-testid="stMain"] [data-testid="stDataFrame"] {
            border-radius: 10px !important;
            border: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
            overflow: hidden !important;
        }
        [data-testid="stMain"] [data-testid="stDataFrame"] button {
            min-height: 1.9rem !important;
            border-radius: 7px !important;
            box-shadow: none !important;
        }
        [data-testid="stMain"] [data-testid="stDataFrame"] [data-testid="stElementToolbar"] {
            opacity: .35;
            transition: opacity .15s ease;
        }
        [data-testid="stMain"] [data-testid="stDataFrame"]:hover [data-testid="stElementToolbar"] {
            opacity: 1;
        }
        [data-testid="stMain"] [data-testid="stTabs"] [role="tablist"] {
            gap: .2rem !important;
            margin-bottom: .5rem !important;
        }
        [data-testid="stMain"] [data-testid="stTabs"] [role="tab"] {
            min-height: 2.35rem !important;
            padding: .35rem .65rem !important;
        }
        [data-testid="stMain"] [data-testid="stFileUploaderDropzone"] {
            min-height: 5.5rem !important;
            padding: .75rem !important;
        }
        [data-testid="stMain"] div[data-testid="stButton"] button,
        [data-testid="stMain"] [data-testid="stDownloadButton"] button {
            min-height: 2.35rem;
        }
        [data-testid="stMain"] hr { margin: .65rem 0 !important; }
        [data-testid="stMain"] h3 { margin-bottom: .2rem !important; }

        @media (max-width: 720px) {
            [data-testid="stMain"] .block-container {
                padding-top: .7rem !important;
                padding-left: .65rem !important;
                padding-right: .65rem !important;
            }
            [data-testid="stMetric"],
            [class*="st-key-rz_metric_card_"] button,
            [class*="st-key-rz_action_card_"] button,
            [class*="st-key-rz_quick_card_"] button {
                min-height: 54px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, *, key: str, help_text: str | None = None) -> bool:
    """Render a compact, full-surface metric that can lead to a related workspace."""
    return st.button(
        f"{label}  ·  {value}  →",
        key=f"rz_metric_card_{key}",
        width="stretch",
        help=help_text,
    )


def navigation_card(label: str, *, key: str, help_text: str | None = None) -> bool:
    """Render a calm full-surface link for a product tool."""
    return st.button(
        f"{label}  →",
        key=f"rz_nav_card_{key}",
        width="stretch",
        help=help_text,
    )
