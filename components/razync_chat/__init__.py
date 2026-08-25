from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_COMPONENT_PATH = Path(__file__).resolve().parent
_component = components.declare_component("razync_chat_v7", path=str(_COMPONENT_PATH))


def razync_chat(
    *,
    messages: list[dict[str, Any]],
    quick_actions: list[dict[str, str]] | None = None,
    action_card: dict[str, Any] | None = None,
    receipt_card: dict[str, Any] | None = None,
    feedback_enabled: bool = False,
    is_loading: bool = False,
    title: str = "Razync",
    subtitle: str = "Assistente online",
    placeholder: str = "Pergunte ao Razync...",
    theme: str = "light",
    key: str = "razync_chat_v7",
) -> dict[str, Any] | None:
    """Renderiza o chat isolado e retorna eventos enviados pelo frontend.

    Eventos previstos:
    - {"action": "send", "text": "...", "event_id": "..."}
    - {"action": "quick_prompt", "text": "...", "event_id": "..."}
    - {"action": "confirm_action" | "cancel_action" | "review_action", "event_id": "..."}
    - {"action": "update_action", "values": {...}, "event_id": "..."}
    - {"action": "upload_document" | "upload_audio", "data": "base64", ...}
    - {"action": "open_receipt" | "undo_action", "event_id": "..."}
    - {"action": "close", "event_id": "..."}
    - {"action": "open_full", "event_id": "..."}
    """
    return _component(
        messages=messages,
        quick_actions=quick_actions or [],
        action_card=action_card,
        receipt_card=receipt_card,
        feedback_enabled=bool(feedback_enabled),
        is_loading=bool(is_loading),
        title=str(title),
        subtitle=str(subtitle),
        placeholder=str(placeholder),
        theme="dark" if str(theme).lower() == "dark" else "light",
        default=None,
        key=key,
    )
