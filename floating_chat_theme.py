from __future__ import annotations

import streamlit as st


def inject_floating_assistant_styles() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer, header[data-testid="stHeader"], [data-testid="stToolbar"],
        [data-testid="stDecoration"], [data-testid="stStatusWidget"],
        [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"] {
            display: none !important;
            visibility: hidden !important;
        }

        .st-key-floating_ai_launcher {
            position: fixed !important;
            right: .9rem !important;
            bottom: .9rem !important;
            z-index: 999990 !important;
            width: auto !important;
        }
        .st-key-floating_ai_launcher [data-testid="stButton"] button {
            min-height: 42px !important;
            padding: .48rem .78rem !important;
            border: 0 !important;
            border-radius: 999px !important;
            color: #fff !important;
            background: #087ea4 !important;
            box-shadow: 0 8px 22px rgba(2,49,69,.18) !important;
            font-size: .76rem !important;
            font-weight: 700 !important;
        }

        .st-key-floating_ai_panel {
            position: fixed !important;
            right: .8rem !important;
            bottom: .8rem !important;
            z-index: 999995 !important;
            width: min(350px, calc(100vw - 1.2rem)) !important;
            height: min(500px, calc(100vh - 1.2rem)) !important;
            min-height: 380px !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 14px !important;
            background: var(--rz-surface) !important;
            box-shadow: 0 18px 50px rgba(2,27,43,.18), 0 2px 8px rgba(2,27,43,.05) !important;
        }
        .st-key-floating_ai_panel > div,
        .st-key-floating_ai_panel > div > [data-testid="stVerticalBlock"] {
            height: 100% !important;
            min-height: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
            overflow: hidden !important;
        }

        .rz-chat-head {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 50px !important;
            display: flex !important;
            align-items: center !important;
            gap: .55rem !important;
            padding: .48rem .62rem !important;
            border-bottom: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            z-index: 3 !important;
        }
        .rz-chat-avatar {
            width: 30px !important;
            height: 30px !important;
            display: grid !important;
            place-items: center !important;
            flex: 0 0 30px !important;
            border-radius: 9px !important;
            color: #fff !important;
            background: #087ea4 !important;
            font-size: .58rem !important;
            font-weight: 850 !important;
        }
        .rz-chat-title strong {
            display: block !important;
            color: var(--rz-text) !important;
            font-size: .8rem !important;
            line-height: 1.1 !important;
        }
        .rz-chat-title span {
            display: flex !important;
            align-items: center !important;
            gap: .28rem !important;
            margin-top: .12rem !important;
            color: var(--rz-muted) !important;
            font-size: .57rem !important;
        }
        .rz-chat-title span i {
            width: 5px !important;
            height: 5px !important;
            border-radius: 50% !important;
            background: #20b26b !important;
        }

        .st-key-floating_ai_close {
            position: absolute !important;
            top: .42rem !important;
            right: .38rem !important;
            z-index: 7 !important;
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
            font-size: .88rem !important;
        }
        .st-key-floating_ai_close [data-testid="stButton"] button:hover {
            color: var(--rz-text) !important;
            background: var(--rz-soft) !important;
        }

        .st-key-floating_ai_thread {
            position: absolute !important;
            top: 50px !important;
            right: 0 !important;
            bottom: 58px !important;
            left: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: .68rem .68rem .55rem !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            overscroll-behavior: contain !important;
            background: var(--rz-surface) !important;
            scrollbar-width: thin !important;
            scrollbar-color: color-mix(in srgb, var(--rz-muted) 25%, transparent) transparent !important;
        }
        .st-key-floating_ai_thread::-webkit-scrollbar { width: 4px !important; }
        .st-key-floating_ai_thread::-webkit-scrollbar-track { background: transparent !important; }
        .st-key-floating_ai_thread::-webkit-scrollbar-thumb {
            border-radius: 999px !important;
            background: color-mix(in srgb, var(--rz-muted) 24%, transparent) !important;
        }
        .st-key-floating_ai_thread > div,
        .st-key-floating_ai_thread [data-testid="stVerticalBlock"] {
            overflow: visible !important;
        }

        .rz-chat-messages {
            display: flex !important;
            flex-direction: column !important;
            gap: .52rem !important;
            width: 100% !important;
        }
        .rz-msg {
            display: flex !important;
            width: 100% !important;
        }
        .rz-msg > div {
            max-width: 88% !important;
            color: var(--rz-text) !important;
            font-size: .76rem !important;
            line-height: 1.45 !important;
            overflow-wrap: anywhere !important;
        }
        .rz-msg p { margin: 0 0 .38rem !important; }
        .rz-msg p:last-child { margin-bottom: 0 !important; }
        .rz-msg-assistant { justify-content: flex-start !important; }
        .rz-msg-assistant > div {
            padding: .1rem .08rem !important;
            background: transparent !important;
        }
        .rz-msg-user { justify-content: flex-end !important; }
        .rz-msg-user > div {
            padding: .46rem .6rem !important;
            border-radius: 13px 13px 4px 13px !important;
            background: color-mix(in srgb, var(--rz-primary-soft) 84%, var(--rz-surface)) !important;
        }
        .rz-typing > div {
            display: flex !important;
            gap: .24rem !important;
            align-items: center !important;
            min-height: 20px !important;
        }
        .rz-typing span {
            width: 5px !important;
            height: 5px !important;
            border-radius: 50% !important;
            background: var(--rz-muted) !important;
            animation: rzTyping 1.2s infinite ease-in-out !important;
        }
        .rz-typing span:nth-child(2) { animation-delay: .14s !important; }
        .rz-typing span:nth-child(3) { animation-delay: .28s !important; }
        @keyframes rzTyping {
            0%, 60%, 100% { opacity: .28; transform: translateY(0); }
            30% { opacity: 1; transform: translateY(-2px); }
        }

        .st-key-floating_ai_thread [data-testid="stSpinner"] {
            margin: .35rem 0 !important;
            min-height: 20px !important;
        }
        .st-key-floating_ai_thread [data-testid="stSpinner"] p {
            color: var(--rz-muted) !important;
            font-size: .66rem !important;
        }
        .st-key-floating_ai_thread .stAlert {
            padding: .45rem .5rem !important;
            border-radius: 8px !important;
            font-size: .68rem !important;
        }
        .st-key-floating_ai_thread [data-testid="stDownloadButton"] button,
        .st-key-floating_ai_thread [data-testid="stButton"] button {
            min-height: 31px !important;
            padding: .32rem .5rem !important;
            border-radius: 8px !important;
            font-size: .66rem !important;
            box-shadow: none !important;
        }

        .st-key-floating_ai_composer {
            position: absolute !important;
            right: 0 !important;
            bottom: 0 !important;
            left: 0 !important;
            height: 58px !important;
            margin: 0 !important;
            padding: .48rem .56rem !important;
            border-top: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            overflow: hidden !important;
            z-index: 4 !important;
        }
        .st-key-floating_ai_composer [data-testid="stHorizontalBlock"] {
            gap: .34rem !important;
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
            padding: 0 .62rem !important;
            color: var(--rz-text) !important;
            background: transparent !important;
            font-size: .74rem !important;
        }
        .st-key-floating_ai_composer [data-testid="stButton"] button {
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
            font-size: .8rem !important;
        }

        @media (max-width: 700px) {
            .st-key-floating_ai_panel {
                right: .45rem !important;
                bottom: .45rem !important;
                width: min(340px, calc(100vw - .9rem)) !important;
                height: min(480px, calc(100vh - .9rem)) !important;
                min-height: 360px !important;
                border-radius: 13px !important;
            }
            .st-key-floating_ai_launcher { right: .55rem !important; bottom: .55rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
