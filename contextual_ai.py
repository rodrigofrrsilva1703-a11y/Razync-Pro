from __future__ import annotations

import streamlit as st


_CONTEXT_KEY = "razync_ai_pending_context"
_QUESTION_KEY = "razync_ai_pending_question"


def open_assistant_with_context(
    *,
    navigate,
    source: str,
    title: str,
    question: str,
    detail: str | None = None,
    page: str | None = None,
) -> None:
    """Open the existing assistant with a safe product context prepared by the current tool."""
    st.session_state[_QUESTION_KEY] = question
    st.session_state[_CONTEXT_KEY] = {
        "source": source,
        "title": title,
        "detail": detail or "",
        "page": page or "",
    }
    navigate("Assistente Razync")


def contextual_ai_button(
    label: str,
    *,
    key: str,
    navigate,
    source: str,
    title: str,
    question: str,
    detail: str | None = None,
    page: str | None = None,
    help_text: str | None = None,
) -> bool:
    """Render a single safe handoff button; no mutation is executed here."""
    clicked = st.button(
        label,
        key=f"rz_context_ai_{key}",
        icon=":material/auto_awesome:",
        width="stretch",
        help=help_text,
    )
    if clicked:
        open_assistant_with_context(
            navigate=navigate,
            source=source,
            title=title,
            question=question,
            detail=detail,
            page=page,
        )
    return clicked
