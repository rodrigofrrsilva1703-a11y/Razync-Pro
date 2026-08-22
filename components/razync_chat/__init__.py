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
    resources: dict[str, Any] | None = None,
    max_document_bytes: int = 6 * 1024 * 1024,
    max_audio_bytes: int = 10 * 1024 * 1024,
    is_loading: bool = False,
    title: str = "Razync",
    subtitle: str = "Assistente online",
    placeholder: str = "Pergunte ao Razync...",
    theme: str = "light",
    key: str = "razync_chat_v7",
) -> dict[str, Any] | None:
    """Renderiza o chat isolado e retorna eventos enviados pelo frontend."""
    return _component(
        messages=messages,
        quick_actions=quick_actions or [],
        action_card=action_card,
        receipt_card=receipt_card,
        resources=resources or {"downloads": [], "note": None, "route": None, "route_label": None},
        max_document_bytes=max(1, int(max_document_bytes)),
        max_audio_bytes=max(1, int(max_audio_bytes)),
        is_loading=bool(is_loading),
        title=str(title),
        subtitle=str(subtitle),
        placeholder=str(placeholder),
        theme="dark" if str(theme).lower() == "dark" else "light",
        default=None,
        key=key,
    )
