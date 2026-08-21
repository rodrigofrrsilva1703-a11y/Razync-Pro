from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from assistant_workspace import render_floating_ai_assistant
from navigation_config import SIDEBAR_GROUPS, SIDEBAR_ICONS, SIDEBAR_LABELS, SIDEBAR_SECONDARY_GROUPS
from onboarding_tools import onboarding_progress


def _floating_chat_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-floating_ai_shortcut {
            position: fixed;
            right: 1.35rem;
            bottom: 1.2rem;
            z-index: 100000;
            width: auto !important;
            max-width: min(455px, calc(100vw - 1.4rem));
        }
        .st-key-floating_ai_shortcut > div { width: auto !important; }
        .st-key-floating_ai_shortcut [data-testid="stPopover"] > button {
            min-height: 3.15rem !important;
            padding: .68rem 1rem .68rem .82rem !important;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 46%, var(--rz-border)) !important;
            border-radius: 999px !important;
            color: #fff !important;
            background: linear-gradient(135deg, #071a2a 0%, var(--rz-primary) 100%) !important;
            box-shadow: 0 14px 34px rgba(2, 36, 58, .26) !important;
            font-size: .86rem !important;
            font-weight: 720 !important;
            letter-spacing: -.01em;
            transition: transform .16s ease, box-shadow .16s ease !important;
        }
        .st-key-floating_ai_shortcut [data-testid="stPopover"] > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 40px rgba(2, 36, 58, .32) !important;
        }

        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) {
            width: min(445px, calc(100vw - 1rem)) !important;
            height: min(720px, calc(100vh - 4.7rem)) !important;
            max-height: min(720px, calc(100vh - 4.7rem)) !important;
            padding: 0 !important;
            overflow: hidden !important;
            border: 1px solid color-mix(in srgb, var(--rz-border) 88%, transparent) !important;
            border-radius: 20px !important;
            background: var(--rz-surface) !important;
            box-shadow: 0 28px 80px rgba(2, 27, 43, .24), 0 8px 24px rgba(2, 27, 43, .08) !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) > div {
            display: flex !important;
            flex-direction: column !important;
            height: 100% !important;
            padding: 0 !important;
            overflow: hidden !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-head {
            position: relative !important;
            top: auto !important;
            flex: 0 0 auto;
            min-height: 68px;
            margin: 0 !important;
            padding: .84rem .95rem !important;
            border: 0 !important;
            border-bottom: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
            backdrop-filter: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-head-icon {
            width: 40px !important;
            height: 40px !important;
            flex-basis: 40px !important;
            border-radius: 13px !important;
            background: linear-gradient(145deg, #061a29, var(--rz-primary)) !important;
            box-shadow: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-head strong {
            color: var(--rz-text) !important;
            font-size: .95rem !important;
            letter-spacing: -.018em !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-head span {
            color: var(--rz-muted) !important;
            font-size: .68rem !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-online {
            width: 6px; height: 6px;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-head-badge,
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-examples,
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_quick_actions {
            display: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_messages {
            flex: 1 1 auto !important;
            min-height: 0 !important;
            max-height: none !important;
            overflow-y: auto !important;
            margin: 0 !important;
            padding: .9rem .82rem .65rem !important;
            background: color-mix(in srgb, var(--rz-soft) 62%, var(--rz-surface)) !important;
            scrollbar-width: thin;
            scrollbar-color: var(--rz-border) transparent;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_messages [data-testid="stChatMessage"] {
            width: fit-content !important;
            max-width: 86% !important;
            min-width: 0 !important;
            margin: .28rem 0 .58rem !important;
            padding: .62rem .74rem !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 16px !important;
            background: var(--rz-surface) !important;
            box-shadow: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_messages [aria-label="Chat message from user"] {
            margin-left: auto !important;
            border-color: color-mix(in srgb, var(--rz-primary) 18%, var(--rz-border)) !important;
            border-bottom-right-radius: 5px !important;
            background: color-mix(in srgb, var(--rz-primary-soft) 86%, var(--rz-surface)) !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_messages [aria-label="Chat message from assistant"] {
            margin-right: auto !important;
            border-bottom-left-radius: 5px !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_messages [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
            font-size: .82rem !important;
            line-height: 1.55 !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_messages [data-testid*="Avatar"] {
            display: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_composer {
            flex: 0 0 auto !important;
            margin: 0 !important;
            padding: .72rem .78rem .5rem !important;
            border-top: 1px solid var(--rz-border) !important;
            background: var(--rz-surface) !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_composer [data-testid="stChatInput"] {
            min-height: 46px !important;
            border: 1px solid var(--rz-border) !important;
            border-radius: 15px !important;
            background: var(--rz-soft) !important;
            box-shadow: none !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_composer [data-testid="stChatInput"]:focus-within {
            border-color: color-mix(in srgb, var(--rz-primary) 65%, var(--rz-border)) !important;
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--rz-primary) 10%, transparent) !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .st-key-floating_ai_composer textarea {
            min-height: 44px !important;
            padding-top: .72rem !important;
            font-size: .82rem !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .rz-ai-safety {
            flex: 0 0 auto;
            margin: 0 !important;
            padding: .1rem .9rem .55rem !important;
            border: 0 !important;
            color: var(--rz-muted) !important;
            font-size: .62rem !important;
            background: var(--rz-surface) !important;
        }
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) .stAlert,
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) [data-testid="stDownloadButton"],
        body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) [data-testid="stButton"] {
            margin-left: .78rem !important;
            margin-right: .78rem !important;
        }
        .st-key-floating_ai_full_link [data-testid="stButton"] button {
            min-height: 2.15rem !important;
            border: 0 !important;
            color: var(--rz-muted) !important;
            background: transparent !important;
            box-shadow: none !important;
            font-size: .7rem !important;
        }
        .st-key-floating_ai_full_link [data-testid="stButton"] button:hover {
            color: var(--rz-primary) !important;
            background: var(--rz-primary-soft) !important;
        }
        @media (max-width: 700px) {
            .st-key-floating_ai_shortcut { right: .7rem; bottom: .7rem; }
            .st-key-floating_ai_shortcut [data-testid="stPopover"] > button { min-height: 2.9rem !important; padding: .58rem .82rem !important; }
            body [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) {
                width: calc(100vw - .7rem) !important;
                height: min(78vh, 680px) !important;
                max-height: min(78vh, 680px) !important;
                border-radius: 17px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_floating_assistant(page: str, user: dict, navigate) -> None:
    if page == "Assistente Razync":
        return

    with st.container(key="floating_ai_shortcut"):
        with st.popover("✦ Razync IA"):
            render_floating_ai_assistant(user=user, page=page, navigate=navigate)
            with st.container(key="floating_ai_full_link"):
                if st.button("Abrir conversa completa ↗", key="floating_ai_open_full", width="stretch"):
                    navigate("Assistente Razync")
            _floating_chat_styles()


def render_sidebar(
    *,
    profile: dict,
    user: dict,
    transactions: pd.DataFrame,
    das_rows: list,
    documents: list,
    page: str,
    brand_logo_data_uri: str,
    navigate,
    refresh_data,
    logout,
) -> None:
    business_sidebar = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"

    with st.sidebar:
        st.markdown(
            f"""
            <div class="rz-side-brand">
              <img src="{brand_logo_data_uri}" alt="Razync Pro">
              <div>
                <strong>Razync<em>PRO</em></strong>
                <span>{escape(str(business_sidebar))}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="sidebar_navigation"):
            if st.button(
                SIDEBAR_LABELS["Dashboard"],
                key="grouped_nav_dashboard",
                icon=SIDEBAR_ICONS["Dashboard"],
                disabled=page == "Dashboard",
                width="stretch",
            ):
                navigate("Dashboard")

            for group_title, destinations in SIDEBAR_GROUPS.items():
                with st.expander(group_title, expanded=page in destinations):
                    for destination in destinations:
                        if st.button(
                            SIDEBAR_LABELS[destination],
                            key=f"grouped_nav_{destination}",
                            icon=SIDEBAR_ICONS[destination],
                            disabled=page == destination,
                            width="stretch",
                        ):
                            navigate(destination)

            secondary_pages = [item for pages in SIDEBAR_SECONDARY_GROUPS.values() for item in pages]
            with st.expander("Mais ferramentas", expanded=page in secondary_pages):
                for section_name, destinations in SIDEBAR_SECONDARY_GROUPS.items():
                    st.caption(section_name.upper())
                    for destination in destinations:
                        if st.button(
                            SIDEBAR_LABELS[destination],
                            key=f"secondary_nav_{destination}",
                            icon=SIDEBAR_ICONS[destination],
                            disabled=page == destination,
                            width="stretch",
                        ):
                            navigate(destination)

            setup_progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(documents))
            if setup_progress["percent"] < 100:
                st.divider()
                if st.button(
                    f"Configurar meu MEI · {setup_progress['percent']}%",
                    key="sidebar_onboarding",
                    icon=":material/checklist:",
                    disabled=page == "Primeiros Passos",
                    width="stretch",
                ):
                    navigate("Primeiros Passos")

        st.divider()
        with st.expander("Conta e preferências"):
            account_name = str(user.get("name") or "Minha conta")
            account_email = str(user.get("email") or "").strip()
            st.markdown(f"**{account_name}**")
            if account_email:
                st.markdown(f'<div class="rz-side-account">{escape(account_email)}</div>', unsafe_allow_html=True)
            st.selectbox("Aparência", ["Claro", "Escuro"], key="ui_theme")
            if st.button("Atualizar dados", key="sidebar_refresh", icon=":material/refresh:", width="stretch"):
                refresh_data()
            if st.button("Sair", key="sidebar_logout", width="stretch"):
                logout()

    _render_floating_assistant(page, user, navigate)
