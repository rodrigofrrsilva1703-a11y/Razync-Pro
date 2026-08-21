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
_OPEN_KEY = "razync_floating_open"


def inject_floating_assistant_styles() -> None:
    st.markdown(
        """
        <style>
        #MainMenu,
        footer,
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        [data-testid="stToolbarActions"] {
            display: none !important;
            visibility: hidden !important;
        }

        .st-key-floating_ai_launcher {
            position: fixed !important;
            right: 1.2rem !important;
            bottom: 1.15rem !important;
            z-index: 999990 !important;
            width: auto !important;
        }
        .st-key-floating_ai_launcher > div { width: auto !important; }
        .st-key-floating_ai_launcher [data-testid="stButton"] button {
            min-height: 50px !important;
            padding: .65rem 1rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 42%, var(--rz-border)) !important;
            border-radius: 999px !important;
            color: #fff !important;
            background: linear-gradient(135deg, #061a29 0%, var(--rz-primary) 100%) !important;
            box-shadow: 0 14px 34px rgba(2, 36, 58, .24) !important;
            font-size: .84rem !important;
            font-weight: 760 !important;
        }
        .st-key-floating_ai_launcher [data-testid="stButton"] button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 18px 42px rgba(2, 36, 58, .30) !important;
        }

        .st-key-floating_ai_panel {
            --rz-chat-h: min(680px, calc(100vh - 2rem));
            position: fixed !important;
            right: 1rem !important;
            bottom: 1rem !important;
            z-index: 999995 !important;
            width: min(420px, calc(100vw - 2rem)) !important;
            height: var(--rz-chat-h) !important;
            min-height: 430px !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            border: 1px solid color-mix(in srgb, var(--rz-border) 94%, transparent) !important;
            border-radius: 20px !important;
            background: var(--rz-surface) !important;
            box-shadow: 0 28px 80px rgba(2, 27, 43, .23), 0 7px 22px rgba(2, 27, 43, .08) !important;
        }
        .st-key-floating_ai_panel > div {
            height: 100% !important;
            min-height: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }
        .st-key-floating_ai_panel > div > [data-testid="stVerticalBlock"] {
            height: 100% !important;
            min-height: 0 !important;
            gap: 0 !important;
            overflow: hidden !important;
        }

        .rz-floating-head {
            height: 66px;
            display: flex;
            align-items: center;
            gap: .72rem;
            padding: .75rem .9rem;
            border-bottom: 1px solid var(--rz-border);
            background: var(--rz-surface);
        }
        .rz-floating-avatar {
            width: 39px; height: 39px; flex: 0 0 39px;
            display: grid; place-items: center;
            border-radius: 13px;
            color: #fff;
            background: linear-gradient(145deg, #061a29, var(--rz-primary));
            font-size: .72rem; font-weight: 900; letter-spacing: -.03em;
        }
        .rz-floating-head-copy { min-width: 0; flex: 1; }
        .rz-floating-head-copy strong {
            display: block; color: var(--rz-text); font-size: .94rem;
            font-weight: 780; letter-spacing: -.018em;
        }
        .rz-floating-head-copy span {
            display: flex; align-items: center; gap: .38rem;
            margin-top: .08rem; color: var(--rz-muted); font-size: .66rem;
        }
        .rz-floating-online {
            width: 6px; height: 6px; border-radius: 50%;
            background: #18a66a; box-shadow: 0 0 0 3px rgba(24,166,106,.10);
        }
        .rz-floating-ai-badge {
            padding: .28rem .46rem; margin-right: 2.1rem;
            border: 1px solid var(--rz-border); border-radius: 999px;
            color: var(--rz-muted); background: var(--rz-soft);
            font-size: .57rem; font-weight: 800; letter-spacing: .06em;
        }

        .st-key-floating_ai_close {
            position: absolute !important;
            top: .62rem !important;
            right: .58rem !important;
            z-index: 4 !important;
            width: 34px !important;
        }
        .st-key-floating_ai_close [data-testid="stButton"] button {
            width: 34px !important; min-width: 34px !important; height: 34px !important;
            min-height: 34px !important; padding: 0 !important;
            border: 0 !important; border-radius: 10px !important;
            color: var(--rz-muted) !important; background: transparent !important;
            box-shadow: none !important; font-size: 1rem !important;
        }
        .st-key-floating_ai_close [data-testid="stButton"] button:hover {
            color: var(--rz-text) !important; background: var(--rz-soft) !important;
        }

        .st-key-floating_ai_thread {
            height: calc(var(--rz-chat-h) - 154px) !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: .86rem .78rem .72rem !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            overscroll-behavior: contain !important;
            background: color-mix(in srgb, var(--rz-soft) 58%, var(--rz-surface)) !important;
            scrollbar-width: thin;
            scrollbar-color: color-mix(in srgb, var(--rz-muted) 30%, transparent) transparent;
        }
        .st-key-floating_ai_thread::-webkit-scrollbar { width: 5px; }
        .st-key-floating_ai_thread::-webkit-scrollbar-track { background: transparent; }
        .st-key-floating_ai_thread::-webkit-scrollbar-thumb {
            border-radius: 999px;
            background: color-mix(in srgb, var(--rz-muted) 28%, transparent);
        }
        .st-key-floating_ai_thread > div,
        .st-key-floating_ai_thread [data-testid="stVerticalBlock"] { overflow: visible !important; }

        .st-key-floating_ai_thread [data-testid="stChatMessage"] {
            width: fit-content !important; max-width: 86% !important; min-width: 0 !important;
            margin: .12rem 0 .54rem !important; padding: .58rem .7rem !important;
            border: 1px solid var(--rz-border) !important; border-radius: 15px !important;
            background: var(--rz-surface) !important; box-shadow: 0 1px 2px rgba(2,27,43,.025) !important;
        }
        .st-key-floating_ai_thread [aria-label="Chat message from user"] {
            margin-left: auto !important;
            border-bottom-right-radius: 5px !important;
            border-color: color-mix(in srgb, var(--rz-primary) 18%, var(--rz-border)) !important;
            background: color-mix(in srgb, var(--rz-primary-soft) 84%, var(--rz-surface)) !important;
        }
        .st-key-floating_ai_thread [aria-label="Chat message from assistant"] {
            margin-right: auto !important; border-bottom-left-radius: 5px !important;
        }
        .st-key-floating_ai_thread [data-testid*="Avatar"] { display: none !important; }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] p {
            margin: 0 !important; color: var(--rz-text) !important;
            font-size: .80rem !important; line-height: 1.52 !important;
        }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] ul,
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] ol {
            margin: .35rem 0 .08rem .95rem !important; padding: 0 !important;
            font-size: .79rem !important;
        }
        .st-key-floating_ai_thread [data-testid="stSpinner"] {
            min-height: 22px !important; margin: 0 !important; padding: 0 !important;
        }
        .st-key-floating_ai_thread [data-testid="stSpinner"] p {
            color: var(--rz-muted) !important; font-size: .70rem !important;
        }
        .st-key-floating_ai_thread .stAlert,
        .st-key-floating_ai_thread [data-testid="stDownloadButton"],
        .st-key-floating_ai_thread [data-testid="stButton"] { margin-top: .32rem !important; }
        .st-key-floating_ai_thread [data-testid="stDownloadButton"] button,
        .st-key-floating_ai_thread [data-testid="stButton"] button {
            min-height: 36px !important; border-radius: 10px !important;
            font-size: .72rem !important; box-shadow: none !important;
        }

        .st-key-floating_ai_composer {
            height: 60px !important;
            margin: 0 !important;
            padding: .55rem .7rem .45rem !important;
            border-top: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            overflow: hidden !important;
        }
        .st-key-floating_ai_composer [data-testid="stForm"] {
            margin: 0 !important; padding: 0 !important; border: 0 !important;
            background: transparent !important;
        }
        .st-key-floating_ai_composer [data-testid="stForm"] > div {
            margin: 0 !important; padding: 0 !important;
        }
        .st-key-floating_ai_composer [data-testid="stHorizontalBlock"] {
            gap: .42rem !important; align-items: center !important;
        }
        .st-key-floating_ai_composer [data-testid="stTextInput"] { margin: 0 !important; }
        .st-key-floating_ai_composer [data-testid="stTextInput"] > div > div {
            min-height: 43px !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 14px !important;
            background: var(--rz-soft) !important;
            box-shadow: none !important;
        }
        .st-key-floating_ai_composer [data-testid="stTextInput"] input {
            min-height: 41px !important; color: var(--rz-text) !important;
            background: transparent !important; font-size: .80rem !important;
        }
        .st-key-floating_ai_composer [data-testid="stFormSubmitButton"] button {
            width: 43px !important; min-width: 43px !important; height: 43px !important;
            min-height: 43px !important; padding: 0 !important;
            border: 0 !important; border-radius: 13px !important;
            color: #fff !important; background: var(--rz-primary) !important;
            box-shadow: none !important; font-size: .95rem !important;
        }
        .rz-floating-foot {
            height: 28px; display: flex; align-items: center; justify-content: center;
            margin: 0 !important; padding: 0 .7rem .18rem;
            color: var(--rz-muted); background: var(--rz-surface);
            font-size: .57rem; white-space: nowrap;
        }

        @media (max-width: 700px) {
            .st-key-floating_ai_launcher { right: .65rem !important; bottom: .65rem !important; }
            .st-key-floating_ai_panel {
                --rz-chat-h: min(78vh, 650px);
                right: .45rem !important; bottom: .45rem !important;
                width: calc(100vw - .9rem) !important;
                min-height: 390px !important; border-radius: 17px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
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


def _close_panel() -> None:
    st.session_state[_OPEN_KEY] = False
    st.session_state.pop(_PENDING_KEY, None)
    st.rerun()


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
            key_prefix="floating_v4",
            current_page=page,
            navigate=navigate,
        )
        _render_pending_action(key_prefix="floating_v4_action")
        _render_last_action_undo(key_prefix="floating_v4")

    with st.container(key="floating_ai_composer"):
        with st.form("floating_ai_form", clear_on_submit=True, border=False):
            text_col, send_col = st.columns([8.6, 1.4], gap="small")
            with text_col:
                typed = st.text_input(
                    "Mensagem",
                    key="floating_ai_text_input",
                    label_visibility="collapsed",
                    placeholder="Escreva uma mensagem...",
                )
            with send_col:
                submitted = st.form_submit_button("➤", width="stretch")

    if submitted and typed.strip():
        st.session_state[_PENDING_KEY] = typed.strip()
        st.rerun()

    st.markdown(
        '<div class="rz-floating-foot">Nada é alterado sem sua confirmação.</div>',
        unsafe_allow_html=True,
    )
