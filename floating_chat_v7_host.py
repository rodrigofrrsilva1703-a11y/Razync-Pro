from __future__ import annotations

import streamlit as st

from assistant_workspace import (
    _answer_question,
    _ensure_messages,
    _prepare_resources,
    _session_snapshot,
    _store_turn,
)
from components.razync_chat import razync_chat

_LAST_EVENT_KEY = "razync_chat_v7_last_event"
_OPEN_KEY = "razync_floating_open"


def _public_messages(messages: list[dict]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    for message in messages[-30:]:
        role = "user" if str(message.get("role") or "assistant") == "user" else "assistant"
        content = str(message.get("content") or "").strip()
        if content:
            cleaned.append({"role": role, "content": content})
    return cleaned


def render_isolated_chat_v7(*, user: dict, page: str, navigate) -> None:
    """Renderiza o chat V7 usando um Custom Component isolado."""
    try:
        user_id = int(user.get("id"))
    except (TypeError, ValueError):
        return

    snapshot = _session_snapshot(user_id)
    if snapshot is None:
        return

    profile, transactions, invoices, das_rows, obligations, documents, annual_limit, current_year = snapshot
    messages = _ensure_messages()
    theme = "dark" if str(st.session_state.get("ui_theme") or "").lower().startswith("esc") else "light"

    event = razync_chat(
        messages=_public_messages(messages),
        is_loading=False,
        theme=theme,
        key="razync_chat_v7_instance",
    )
    if not isinstance(event, dict):
        return

    event_id = str(event.get("event_id") or "").strip()
    if event_id and event_id == str(st.session_state.get(_LAST_EVENT_KEY) or ""):
        return
    if event_id:
        st.session_state[_LAST_EVENT_KEY] = event_id

    action = str(event.get("action") or "").strip().lower()
    if action == "open_full":
        st.session_state[_OPEN_KEY] = False
        navigate("Assistente Razync")
        return
    if action == "close":
        st.session_state[_OPEN_KEY] = False
        st.rerun()
    if action != "send":
        return

    question = str(event.get("text") or "").strip()
    if not question:
        return

    result = _answer_question(
        question,
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        annual_limit=annual_limit,
        current_year=current_year,
        current_page=page,
    )
    resources = _prepare_resources(
        question,
        profile=profile,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        current_year=current_year,
    )
    _store_turn(question, result["answer"], resources)
    st.session_state["razync_ai_flash_notices"] = result["notices"]
    st.rerun()
