from __future__ import annotations

import streamlit as st


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

        /* Launcher compacto, inspirado em mensageiros. */
        .st-key-floating_ai_launcher {
            position: fixed !important;
            right: 1rem !important;
            bottom: 1rem !important;
            z-index: 999990 !important;
            width: auto !important;
        }
        .st-key-floating_ai_launcher > div { width: auto !important; }
        .st-key-floating_ai_launcher [data-testid="stButton"] button {
            min-height: 44px !important;
            padding: .5rem .82rem !important;
            border: 0 !important;
            border-radius: 999px !important;
            color: #fff !important;
            background: #087ea4 !important;
            box-shadow: 0 8px 24px rgba(2, 49, 69, .18) !important;
            font-size: .78rem !important;
            font-weight: 700 !important;
        }

        /* Painel pequeno, com proporção de side-chat e sem espaço morto. */
        .st-key-floating_ai_panel {
            --rz-chat-w: 360px;
            --rz-chat-h: min(560px, calc(100vh - 1.5rem));
            position: fixed !important;
            right: .75rem !important;
            bottom: .75rem !important;
            z-index: 999995 !important;
            width: min(var(--rz-chat-w), calc(100vw - 1.5rem)) !important;
            height: var(--rz-chat-h) !important;
            min-height: 390px !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            border: 1px solid color-mix(in srgb, var(--rz-border) 88%, transparent) !important;
            border-radius: 14px !important;
            background: var(--rz-surface) !important;
            box-shadow: 0 18px 52px rgba(2, 27, 43, .20), 0 2px 8px rgba(2, 27, 43, .05) !important;
        }
        .st-key-floating_ai_panel > div,
        .st-key-floating_ai_panel > div > [data-testid="stVerticalBlock"] {
            height: 100% !important;
            min-height: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
            overflow: hidden !important;
        }

        /* Header semelhante a painéis do Copilot: fino, funcional, sem enfeites. */
        .rz-floating-head {
            height: 52px !important;
            display: flex !important;
            align-items: center !important;
            gap: .58rem !important;
            padding: .5rem .65rem !important;
            border-bottom: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
        }
        .rz-floating-avatar {
            width: 30px !important;
            height: 30px !important;
            flex: 0 0 30px !important;
            display: grid !important;
            place-items: center !important;
            border-radius: 9px !important;
            color: #fff !important;
            background: #087ea4 !important;
            font-size: .6rem !important;
            font-weight: 850 !important;
            letter-spacing: -.03em !important;
        }
        .rz-floating-head-copy { min-width: 0 !important; flex: 1 !important; }
        .rz-floating-head-copy strong {
            display: block !important;
            color: var(--rz-text) !important;
            font-size: .82rem !important;
            font-weight: 750 !important;
            letter-spacing: -.01em !important;
        }
        .rz-floating-head-copy span {
            display: flex !important;
            align-items: center !important;
            gap: .3rem !important;
            margin-top: .04rem !important;
            color: var(--rz-muted) !important;
            font-size: .58rem !important;
        }
        .rz-floating-online {
            width: 5px !important;
            height: 5px !important;
            border-radius: 50% !important;
            background: #20b26b !important;
            box-shadow: none !important;
        }
        .rz-floating-ai-badge { display: none !important; }

        .st-key-floating_ai_close {
            position: absolute !important;
            top: .43rem !important;
            right: .42rem !important;
            z-index: 6 !important;
            width: 30px !important;
        }
        .st-key-floating_ai_close [data-testid="stButton"] button {
            width: 30px !important;
            min-width: 30px !important;
            height: 30px !important;
            min-height: 30px !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 8px !important;
            color: var(--rz-muted) !important;
            background: transparent !important;
            box-shadow: none !important;
            font-size: .9rem !important;
        }
        .st-key-floating_ai_close [data-testid="stButton"] button:hover {
            color: var(--rz-text) !important;
            background: var(--rz-soft) !important;
        }

        /* A conversa ocupa o painel; só ela rola. */
        .st-key-floating_ai_thread {
            height: calc(var(--rz-chat-h) - 108px) !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: .72rem .66rem .5rem !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            overscroll-behavior: contain !important;
            background: var(--rz-surface) !important;
            scrollbar-width: thin !important;
            scrollbar-color: color-mix(in srgb, var(--rz-muted) 26%, transparent) transparent !important;
        }
        .st-key-floating_ai_thread::-webkit-scrollbar { width: 4px !important; }
        .st-key-floating_ai_thread::-webkit-scrollbar-track { background: transparent !important; }
        .st-key-floating_ai_thread::-webkit-scrollbar-thumb {
            border-radius: 999px !important;
            background: color-mix(in srgb, var(--rz-muted) 24%, transparent) !important;
        }
        .st-key-floating_ai_thread > div,
        .st-key-floating_ai_thread [data-testid="stVerticalBlock"] { overflow: visible !important; }

        /* Assistente sem card pesado; usuário em bolha simples. */
        .st-key-floating_ai_thread [data-testid="stChatMessage"] {
            width: auto !important;
            min-width: 0 !important;
            margin: .1rem 0 .62rem !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .st-key-floating_ai_thread [aria-label="Chat message from user"] {
            width: fit-content !important;
            max-width: 78% !important;
            margin-left: auto !important;
            padding: .48rem .62rem !important;
            border-radius: 13px 13px 4px 13px !important;
            color: var(--rz-text) !important;
            background: color-mix(in srgb, var(--rz-primary-soft) 84%, var(--rz-surface)) !important;
        }
        .st-key-floating_ai_thread [aria-label="Chat message from assistant"] {
            max-width: 94% !important;
            margin-right: auto !important;
            padding: .12rem .1rem !important;
        }
        .st-key-floating_ai_thread [data-testid*="Avatar"] { display: none !important; }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] p {
            margin: 0 0 .42rem !important;
            color: var(--rz-text) !important;
            font-size: .76rem !important;
            line-height: 1.48 !important;
        }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] p:last-child { margin-bottom: 0 !important; }
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] ul,
        .st-key-floating_ai_thread [data-testid="stMarkdownContainer"] ol {
            margin: .3rem 0 .4rem .95rem !important;
            padding: 0 !important;
            font-size: .75rem !important;
            line-height: 1.45 !important;
        }
        .st-key-floating_ai_thread [data-testid="stSpinner"] {
            min-height: 20px !important;
            margin: .12rem 0 !important;
            padding: 0 !important;
        }
        .st-key-floating_ai_thread [data-testid="stSpinner"] p {
            color: var(--rz-muted) !important;
            font-size: .68rem !important;
        }

        /* Recursos ficam compactos e dentro do histórico. */
        .st-key-floating_ai_thread .stAlert {
            padding: .5rem .58rem !important;
            border-radius: 9px !important;
            font-size: .7rem !important;
        }
        .st-key-floating_ai_thread [data-testid="stDownloadButton"] button,
        .st-key-floating_ai_thread [data-testid="stButton"] button {
            min-height: 32px !important;
            padding: .35rem .55rem !important;
            border-radius: 8px !important;
            font-size: .68rem !important;
            box-shadow: none !important;
        }
        .st-key-floating_ai_thread [data-testid="stExpander"] {
            border-radius: 9px !important;
            border-color: var(--rz-border) !important;
        }

        /* Composer tipo WhatsApp/Copilot: uma linha limpa no rodapé. */
        .st-key-floating_ai_composer {
            height: 56px !important;
            margin: 0 !important;
            padding: .42rem .55rem !important;
            border-top: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            overflow: hidden !important;
        }
        .st-key-floating_ai_composer [data-testid="stForm"] {
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            background: transparent !important;
        }
        .st-key-floating_ai_composer [data-testid="stForm"] > div {
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-floating_ai_composer [data-testid="stHorizontalBlock"] {
            gap: .36rem !important;
            align-items: center !important;
        }
        .st-key-floating_ai_composer [data-testid="stTextInput"] { margin: 0 !important; }
        .st-key-floating_ai_composer [data-testid="stTextInput"] > div > div {
            min-height: 40px !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 12px !important;
            background: var(--rz-soft) !important;
            box-shadow: none !important;
        }
        .st-key-floating_ai_composer [data-testid="stTextInput"] input {
            min-height: 38px !important;
            padding: 0 .65rem !important;
            color: var(--rz-text) !important;
            background: transparent !important;
            font-size: .75rem !important;
        }
        .st-key-floating_ai_composer [data-testid="stFormSubmitButton"] button {
            width: 40px !important;
            min-width: 40px !important;
            height: 40px !important;
            min-height: 40px !important;
            padding: 0 !important;
            border: 0 !important;
            border-radius: 12px !important;
            color: #fff !important;
            background: #0aa8d4 !important;
            box-shadow: none !important;
            font-size: .82rem !important;
        }
        .rz-floating-foot { display: none !important; }

        @media (max-width: 700px) {
            .st-key-floating_ai_launcher { right: .55rem !important; bottom: .55rem !important; }
            .st-key-floating_ai_panel {
                --rz-chat-h: min(66vh, 540px);
                right: .45rem !important;
                bottom: .45rem !important;
                width: min(350px, calc(100vw - .9rem)) !important;
                min-height: 360px !important;
                border-radius: 13px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
