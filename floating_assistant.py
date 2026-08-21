from __future__ import annotations

import streamlit as st

from assistant_workspace import (
    _answer_question,
    _ensure_messages,
    _prepare_resources,
    _render_last_action_undo,
    _render_notices,
    _render_pending_action,
    _render_resources,
    _session_snapshot,
    _store_turn,
)


_PENDING_KEY = "razync_floating_pending_question"


def _header() -> None:
    st.markdown(
        """
        <span class="rz-ai-shell-marker"></span>
        <div class="rz-floating-head">
          <div class="rz-floating-avatar">RZ</div>
          <div class="rz-floating-head-copy">
            <strong>Razync</strong>
            <span><i class="rz-floating-online"></i> Assistente online</span>
          </div>
          <div class="rz-floating-ai-badge">IA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_history(messages: list[dict]) -> None:
    for message in messages[-10:]:
        role = str(message.get("role") or "assistant")
        with st.chat_message(role):
            st.markdown(str(message.get("content") or ""))


def render_floating_assistant(*, user: dict, page: str, navigate) -> None:
    try:
        user_id = int(user.get("id"))
    except (TypeError, ValueError):
        return

    snapshot = _session_snapshot(user_id)
    if snapshot is None:
        st.caption("O assistente ficará disponível assim que os dados terminarem de carregar.")
        return

    profile, transactions, invoices, das_rows, obligations, documents, annual_limit, current_year = snapshot
    messages = _ensure_messages()
    pending_question = str(st.session_state.get(_PENDING_KEY) or "").strip()

    _header()

    # Tudo que pode crescer fica dentro desta única região rolável.
    with st.container(key="floating_ai_thread"):
        _render_history(messages)

        if pending_question:
            with st.chat_message("user"):
                st.markdown(pending_question)
            with st.chat_message("assistant"):
                with st.spinner("Pensando..."):
                    result = _answer_question(
                        pending_question,
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
                        pending_question,
                        profile=profile,
                        transactions=transactions,
                        invoices=invoices,
                        das_rows=das_rows,
                        obligations=obligations,
                        documents=documents,
                        current_year=current_year,
                    )

            _store_turn(pending_question, result["answer"], resources)
            st.session_state["razync_ai_flash_notices"] = result["notices"]
            st.session_state.pop(_PENDING_KEY, None)
            st.rerun()

        _render_notices(st.session_state.pop("razync_ai_flash_notices", []))
        _render_resources(
            st.session_state.get("razync_ai_last_resources"),
            key_prefix="floating_pro",
            current_page=page,
            navigate=navigate,
        )
        _render_pending_action(key_prefix="floating_pro_action")
        _render_last_action_undo(key_prefix="floating_pro")

    # O composer fica fora da região rolável e permanece sempre visível.
    with st.container(key="floating_ai_composer_pro"):
        typed_question = st.chat_input("Escreva uma mensagem...", key="floating_ai_chat_input_pro")

    if typed_question and typed_question.strip():
        st.session_state[_PENDING_KEY] = typed_question.strip()
        st.rerun()

    st.markdown(
        '<div class="rz-floating-foot">O Razync só altera dados após sua confirmação.</div>',
        unsafe_allow_html=True,
    )
