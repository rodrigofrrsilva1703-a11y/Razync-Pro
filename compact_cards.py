from __future__ import annotations

from html import escape

import streamlit as st


def inject_compact_cards() -> None:
    """Compatibility hook. Card styling now lives in workspace_style.py."""
    return None


def stat_card(
    label: str,
    value: str,
    *,
    detail: str | None = None,
    tone: str = "neutral",
) -> None:
    """Render an informational card in the shared workspace design."""
    safe_tone = tone if tone in {"neutral", "positive", "warning", "danger"} else "neutral"
    detail_html = (
        f'<span class="rz-stat-detail">{escape(detail)}</span>'
        if detail else ""
    )
    symbol = {
        "Entradas": "↙", "Saídas": "↗", "Resultado": "≈", "Resultado anual": "↗",
        "Limite MEI": "◉", "Documentos": "▤", "Notas": "▤", "DAS em atraso": "!",
        "DAS pendentes": "◷",
    }.get(label, "◈")
    st.markdown(
        (
            f'<div class="rz-stat-card is-{safe_tone}">'
            f'<div class="rz-stat-top"><span class="rz-stat-label">{escape(label)}</span>'
            f'<span class="rz-stat-symbol" aria-hidden="true">{symbol}</span></div>'
            f'<strong>{escape(value)}</strong>'
            f'{detail_html}'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, *, key: str, help_text: str | None = None) -> bool:
    """Legacy interactive metric retained only where a KPI really is an action."""
    return st.button(
        f"{label}  →\n\n**{value}**",
        key=f"rz_metric_card_{key}",
        width="stretch",
        help=help_text,
    )


def navigation_card(label: str, *, key: str, help_text: str | None = None) -> bool:
    """Render a compact navigation action for secondary product areas."""
    return st.button(
        f"{label}  →",
        key=f"rz_nav_card_{key}",
        width="stretch",
        help=help_text,
    )
