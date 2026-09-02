from __future__ import annotations

import streamlit as st

from assistant_workspace import _session_snapshot
from floating_chat_v7_host import _process_question


_PENDING_QUESTION_KEY = "razync_ai_pending_question"
_PENDING_CONTEXT_KEY = "razync_ai_pending_context"


def process_pending_floating_question(*, user: dict, page: str) -> None:
    """Consume one prepared consultation inside the floating assistant.

    Context remains local to the product handoff; the existing assistant pipeline
    decides what aggregate data may be used externally.
    """
    question = str(st.session_state.pop(_PENDING_QUESTION_KEY, "") or "").strip()
    if not question:
        return

    # The structured context is only a UI handoff marker. The question itself already
    # carries the user intent and the assistant rebuilds its safe business snapshot.
    st.session_state.pop(_PENDING_CONTEXT_KEY, None)

    try:
        user_id = int(user.get("id"))
    except (TypeError, ValueError):
        return

    snapshot = _session_snapshot(user_id)
    if snapshot is None:
        return
    _process_question(question, snapshot=snapshot, page=page)
