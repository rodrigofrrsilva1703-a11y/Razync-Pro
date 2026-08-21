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


def inject_floating_assistant_styles() -> None:
    st.markdown(
        """
        <style>
        /* Remove o chrome do Streamlit/Community Cloud e deixa o produto com aparência própria. */
        #MainMenu,
        footer,
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"],
        [data-testid="stToolbarActions"],
        [class*="viewerBadge"],
        [class*="ViewerBadge"],
        [class*="manageApp"],
        [class*="ManageApp"] {
            display: none !important;
            visibility: hidden !important;
        }

        .rz-ai-shell-marker { display: none !important; }

        /* Botão flutuante. */
        .st-key-floating_ai_shortcut {
            position: fixed !important;
            right: 1.25rem !important;
            bottom: 1.15rem !important;
            z-index: 999990 !important;
            width: auto !important;
        }
        .st-key-floating_ai_shortcut > div { width: auto !important; }
        .st-key-floating_ai_shortcut [data-testid="stPopover"] > button {
            min-height: 48px !important;
            padding: .62rem .95rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 42%, var(--rz-border)) !important;
            border-radius: 999px !important;
            color: #fff !important;
            background: linear-gradient(135deg, #071a2a 0%, var(--rz-primary) 100%) !important;
            box-shadow: 0 12px 30px rgba(2, 36, 58, .22) !important;
            font-size: .84rem !important;
            font-weight: 760 !important;
            letter-spacing: -.01em !important;
            transition: transform .16s ease, box-shadow .16s ease !important;
        }
        .st-key-floating_ai_shortcut [data-testid="stPopover"] > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 16px 38px rgba(2, 36, 58, .28) !important;
        }

        /* Painel: posição e tamanho independentes do algoritmo de popover do Streamlit. */
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) {
            --rz-chat-h: min(650px, calc(100vh - 7rem));
            position: fixed !important;
            inset: auto 1.25rem 4.95rem auto !important;
            transform: none !important;
            width: min(420px, calc(100vw - 2rem)) !important;
            height: var(--rz-chat-h) !important;
            max-height: var(--rz-chat-h) !important;
            min-height: 420px !important;
            padding: 0 !important;
            overflow: hidden !important;
            border: 1px solid color-mix(in srgb, var(--rz-border) 92%, transparent) !important;
            border-radius: 18px !important;
            background: var(--rz-surface) !important;
            box-shadow: 0 24px 70px rgba(2, 27, 43, .22), 0 6px 20px rgba(2, 27, 43, .08) !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) > div:first-child {
            height: 100% !important;
            max-height: 100% !important;
            padding: 0 !important;
            overflow: hidden !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) [data-radix-popper-arrow-wrapper] {
            display: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        /* Cabeçalho compacto e neutro. */
        .rz-floating-head {
            height: 66px;
            display: flex;
            align-items: center;
            gap: .72rem;
            padding: .72rem .88rem;
            border-bottom: 1px solid var(--rz-border);
            background: var(--rz-surface);
        }
        .rz-floating-avatar {
            width: 38px;
            height: 38px;
            flex: 0 0 38px;
            display: grid;
            place-items: center;
            border-radius: 12px;
            color: #fff;
            background: linear-gradient(145deg, #071a2a, var(--rz-primary));
            font-size: .72rem;
            font-weight: 900;
            letter-spacing: -.03em;
        }
        .rz-floating-head-copy { min-width: 0; flex: 1; }
        .rz-floating-head-copy strong {
            display: block;
            color: var(--rz-text);
            font-size: .93rem;
            font-weight: 780;
            letter-spacing: -.018em;
        }
        .rz-floating-head-copy span {
            display: flex;
            align-items: center;
            gap: .38rem;
            margin-top: .08rem;
            color: var(--rz-muted);
            font-size: .66rem;
        }
        .rz-floating-online {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #18a66a;
            box-shadow: 0 0 0 3px rgba(24,166,106,.10);
        }
        .rz-floating-ai-badge {
            padding: .3rem .48rem;
            border: 1px solid var(--rz-border);
            border-radius: 999px;
            color: var(--rz-muted);
            background: var(--rz-soft);
            font-size: .58rem;
            font-weight: 800;
            letter-spacing: .06em;
        }

        /* Somente esta região rola. Header e composer nunca saem da tela. */
        .st-key-floating_ai_thread {
            height: calc(var(--rz-chat-h) - 152px) !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: .88rem .78rem .7rem !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            overscroll-behavior: contain;
            background: color-mix(in srgb, var(--rz-soft) 54%, var(--rz-surface)) !important;
            scrollbar-width: thin;
            scrollbar-color: color-mix(in srgb, var(--rz-muted) 34%, transparent) transparent;
        }
        .st-key-floating_ai_thread::-webkit-scrollbar { width: 5px; }
        .st-key-floating_ai_thread::-webkit-scrollbar-track { background: transparent; }
        .st-key-floating_ai_thread::-webkit-scrollbar-thumb {
            border-radius: 999px;
            background: color-mix(in srgb, var(--rz-muted) 30%, transparent);
        }

        /* Balões de conversa. */
        .st-key-floating_ai_thread [data-testid="stChatMessage"] {
            width: fit-content !important;
            max-width: 86% !important;
            min-width: 0 !important;
            margin: .16rem 0 .56rem !important;
            padding: .58rem .72rem !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 15px !important;
            background: var(--rz-surface) !important;
            box-shadow: 0 1px 2px rgba(2,27,43,.03) !important;
        }
        .st-key-floating_ai_thread [aria-label="Chat message from user"] {
            margin-left: auto !important;
            border-bottom-right-radius: 5px !important;
            border-color: color-mix(in srgb, var(--rz-primary) 19%, var(--rz-border)) !important;
            background: color-mix(in srgb, var(--rz-primary-soft) 82%, var(--rz-surface)) !important;
        }
        .st-key-floating_ai_thread [aria-label="Chat message from assistant"] {
            margin-right: auto !important;
            border-bottom-left-radius: 5px !important;
        }
        .st-key-floating_ai_thread [data-testid*="Avatar"] {
            display: none !important;
        }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            color: var(--rz-text) !important;
            font-size: .81rem !important;
            line-height: 1.52 !important;
        }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] ul,
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] ol {
            margin: .35rem 0 .05rem 1rem !important;
            padding: 0 !important;
            font-size: .8rem !important;
        }

        /* Loading vira uma bolha discreta dentro da conversa. */
        .st-key-floating_ai_thread [data-testid="stSpinner"] {
            min-height: 24px !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-floating_ai_thread [data-testid="stSpinner"] p {
            color: var(--rz-muted) !important;
            font-size: .72rem !important;
        }

        /* Recursos e confirmações pertencem ao histórico e não empurram o composer. */
        .st-key-floating_ai_thread .stAlert,
        .st-key-floating_ai_thread [data-testid="stDownloadButton"],
        .st-key-floating_ai_thread [data-testid="stButton"] {
            margin-top: .35rem !important;
        }
        .st-key-floating_ai_thread [data-testid="stDownloadButton"] button,
        .st-key-floating_ai_thread [data-testid="stButton"] button {
            min-height: 38px !important;
            border-radius: 11px !important;
            font-size: .74rem !important;
            box-shadow: none !important;
        }
        .st-key-floating_ai_thread [data-testid="stExpander"] {
            border-color: var(--rz-border) !important;
            border-radius: 12px !important;
            background: var(--rz-surface) !important;
        }

        /* Composer fixo visualmente no rodapé do painel. */
        .st-key-floating_ai_composer_pro {
            height: 58px !important;
            margin: 0 !important;
            padding: .52rem .7rem .34rem !important;
            border-top: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
        }
        .st-key-floating_ai_composer_pro [data-testid="stChatInput"] {
            min-height: 44px !important;
            overflow: hidden !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 14px !important;
            background: var(--rz-soft) !important;
            box-shadow: none !important;
        }
        .st-key-floating_ai_composer_pro [data-testid="stChatInput"]:focus-within {
            border-color: color-mix(in srgb, var(--rz-primary) 58%, var(--rz-border)) !important;
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--rz-primary) 9%, transparent) !important;
        }
        .st-key-floating_ai_composer_pro textarea {
            min-height: 42px !important;
            padding-top: .67rem !important;
            color: var(--rz-text) !important;
            background: transparent !important;
            font-size: .8rem !important;
        }
        .st-key-floating_ai_composer_pro [data-testid="stChatInputSubmitButton"] {
            color: #fff !important;
            background: var(--rz-primary) !important;
            border-radius: 10px !important;
        }
        .rz-floating-foot {
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 !important;
            padding: 0 .7rem .18rem;
            color: var(--rz-muted);
            background: var(--rz-surface);
            font-size: .58rem;
            white-space: nowrap;
        }

        @media (max-width: 700px) {
            .st-key-floating_ai_shortcut { right: .65rem !important; bottom: .65rem !important; }
            .st-key-floating_ai_shortcut [data-testid="stPopover"] > button {
                min-height: 44px !important;
                padding: .55rem .78rem !important;
            }
            body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) {
                --rz-chat-h: min(72vh, 620px);
                inset: auto .45rem 4.15rem auto !important;
                width: calc(100vw - .9rem) !important;
                min-height: 390px !important;
                border-radius: 16px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    inject_floating_assistant_styles()

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

    # Tudo que cresce fica dentro da thread. O composer nunca entra na rolagem.
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

    with st.container(key="floating_ai_composer_pro"):
        typed_question = st.chat_input("Escreva uma mensagem...", key="floating_ai_chat_input_pro")

    if typed_question and typed_question.strip():
        st.session_state[_PENDING_KEY] = typed_question.strip()
        st.rerun()

    st.markdown(
        '<div class="rz-floating-foot">O Razync só altera dados após sua confirmação.</div>',
        unsafe_allow_html=True,
    )
