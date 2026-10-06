from __future__ import annotations

import streamlit as st


def inject_compact_cards() -> None:
    """Compatibility hook. Card styling now lives in workspace_style.py."""
    return None


def metric_card(label: str, value: str, *, key: str, help_text: str | None = None) -> bool:
    """Render a compact, full-surface metric that can lead to a related workspace."""
    return st.button(
        f"{label}  →\n\n**{value}**",
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
