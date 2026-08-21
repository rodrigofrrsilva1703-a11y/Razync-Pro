from __future__ import annotations

from html import escape

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
_OPEN_KEY = "razync_floating_open"
_INPUT_KEY = "razync_floating_input"


def _safe_message_html(text: str) -> str:
    safe = escape(str(text or "")).replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [part.strip() for part in safe.split("\n\n") if part.strip()]
    if not paragraphs:
        return ""
    return "".join(f"<p>{part.replace(chr(10), '<br>')}</p>" for part in paragraphs)


def _render_header() -> None:
    st.markdown(
        """
        <div class="rz-chat-head">
          <div class="rz-chat-avatar">RZ</div>
          <div class="rz-chat-title">
            <strong>Razync</strong>
            <span><i></i> online</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_history(messages: list[dict], pending_question: str = "") -> None:
    rows: list[str] = []
    for message in messages[-10:]:
        role = "user" if str(message.get("role") or "assistant") == "user" else "assistant"
        body = _safe_message_html(str(message.get("content") or ""))
        rows.append(f'<div class="rz-msg rz-msg-{role}"><div>{body}</div></div>')
    if pending_question:
        rows.append(
            f'<div class="rz-msg rz-msg-user"><div>{_safe_message_html(pending_question)}</div></div>'
            '<div class="rz-msg rz-msg-assistant rz-typing"><div><span></span><span></span><span></span></div></div>'
        )
    st.markdown('<div class="rz-chat-messages">' + "".join(rows) + '</div>', unsafe_allow_html=True)


def _close_panel() -> None:
    st.session_state[_OPEN_KEY] = False
    st.session_state.pop(_PENDING_KEY, None)
    st.rerun()


def _queue_message() -> None:
    value = str(st.session_state.get(_INPUT_KEY) or "").strip()
    if value:
        st.session_state[_PENDING_KEY] = value
        st.session_state[_INPUT_KEY] = ""


def _process_pending(
    question: str,
    *,
    profile: dict,
    transactions,
    invoices,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    annual_limit: float,
    current_year: int,
    page: str,
) -> None:
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
    st.session_state.pop(_PENDING_KEY, None)


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

    _render_header()
    with st.container(key="floating_ai_close"):
        if st.button("×", key="floating_ai_close_btn", help="Fechar conversa"):
            _close_panel()

    with st.container(key="floating_ai_thread"):
        _render_history(messages, pending_question)
        if pending_question:
            with st.spinner("Processando sua mensagem..."):
                _process_pending(
                    pending_question,
                    profile=profile,
                    transactions=transactions,
                    invoices=invoices,
                    das_rows=das_rows,
                    obligations=obligations,
                    documents=documents,
                    annual_limit=annual_limit,
                    current_year=current_year,
                    page=page,
                )
            st.rerun()

        _render_notices(st.session_state.pop("razync_ai_flash_notices", []))
        _render_resources(
            st.session_state.get("razync_ai_last_resources"),
            key_prefix="floating_v6",
            current_page=page,
            navigate=navigate,
        )
        _render_pending_action(key_prefix="floating_v6_action")
        _render_last_action_undo(key_prefix="floating_v6")

    with st.container(key="floating_ai_composer"):
        text_col, send_col = st.columns([8.7, 1.3], gap="small")
        with text_col:
            st.text_input(
                "Mensagem",
                key=_INPUT_KEY,
                label_visibility="collapsed",
                placeholder="Pergunte ao Razync...",
            )
        with send_col:
            st.button(
                "➤",
                key="floating_ai_send_btn",
                width="stretch",
                help="Enviar mensagem",
                on_click=_queue_message,
            )
