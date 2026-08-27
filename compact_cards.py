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
            min-height: 82px !important;
            padding: 10px 13px !important;
            border-radius: 11px !important;
        }
        [class*="st-key-rz_action_card_"] button p,
        [class*="st-key-rz_quick_card_"] button p {
            line-height: 1.28 !important;
            font-size: .79rem !important;
        }

        [class*="st-key-rz_metric_card_"] button {
            min-height: 82px !important;
            height: auto !important;
            padding: 10px 13px !important;
            justify-content: flex-start !important;
            text-align: left !important;
            border-radius: 11px !important;
            border: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            box-shadow: var(--rz-shadow-soft) !important;
            transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease !important;
        }
        [class*="st-key-rz_metric_card_"] button:hover {
            transform: translateY(-2px) !important;
            border-color: var(--rz-primary) !important;
            box-shadow: 0 10px 24px rgba(20,45,68,.09) !important;
        }
        [class*="st-key-rz_metric_card_"] button p {
            width: 100% !important;
            text-align: left !important;
            white-space: normal !important;
            line-height: 1.22 !important;
            font-size: .76rem !important;
        }
        [class*="st-key-rz_metric_card_"] button p strong {
            display: inline-block !important;
            margin-top: .18rem !important;
            font-size: 1.28rem !important;
            line-height: 1.05 !important;
            letter-spacing: -.03em !important;
            color: var(--rz-text) !important;
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

        @media (max-width: 720px) {
            [data-testid="stMetric"],
            [class*="st-key-rz_metric_card_"] button,
            [class*="st-key-rz_action_card_"] button,
            [class*="st-key-rz_quick_card_"] button {
                min-height: 76px !important;
            }
            [class*="st-key-rz_metric_card_"] button p strong {
                font-size: 1.18rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, *, key: str, help_text: str | None = None) -> bool:
    """Render a compact, full-surface metric that can lead to a related workspace."""
    return st.button(
        f"{label}\n\n**{value}**\n\nVer detalhes →",
        key=f"rz_metric_card_{key}",
        width="stretch",
        help=help_text,
    )
