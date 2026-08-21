from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from floating_chat_v7_host import render_isolated_chat_v7
from navigation_config import SIDEBAR_GROUPS, SIDEBAR_ICONS, SIDEBAR_LABELS, SIDEBAR_SECONDARY_GROUPS
from onboarding_tools import onboarding_progress


_FLOATING_OPEN_KEY = "razync_floating_open"


def _floating_chat_shell_styles() -> None:
    st.markdown(
        """
        <style>
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
            padding: .52rem .86rem !important;
            border: 0 !important;
            border-radius: 999px !important;
            color: #fff !important;
            background: #087ea4 !important;
            box-shadow: 0 10px 28px rgba(2,49,69,.20) !important;
            font-size: .78rem !important;
            font-weight: 700 !important;
        }
        .st-key-floating_ai_v7_shell {
            position: fixed !important;
            right: .9rem !important;
            bottom: .9rem !important;
            z-index: 999995 !important;
            width: min(360px, calc(100vw - 1.2rem)) !important;
            height: 540px !important;
            max-height: calc(100vh - 1.2rem) !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            background: transparent !important;
        }
        .st-key-floating_ai_v7_shell > div,
        .st-key-floating_ai_v7_shell > div > [data-testid="stVerticalBlock"] {
            margin: 0 !important;
            padding: 0 !important;
            gap: 0 !important;
            overflow: hidden !important;
        }
        .st-key-floating_ai_v7_shell iframe {
            display: block !important;
            width: 100% !important;
            border: 0 !important;
            background: transparent !important;
        }
        @media (max-width: 700px) {
            .st-key-floating_ai_launcher { right: .55rem !important; bottom: .55rem !important; }
            .st-key-floating_ai_v7_shell {
                right: .45rem !important;
                bottom: .45rem !important;
                width: min(350px, calc(100vw - .9rem)) !important;
                height: 500px !important;
                max-height: calc(100vh - .9rem) !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_floating_assistant(page: str, user: dict, navigate) -> None:
    if page == "Assistente Razync":
        return

    _floating_chat_shell_styles()
    is_open = bool(st.session_state.get(_FLOATING_OPEN_KEY, False))
    if is_open:
        with st.container(key="floating_ai_v7_shell"):
            render_isolated_chat_v7(user=user, page=page, navigate=navigate)
        return

    with st.container(key="floating_ai_launcher"):
        if st.button("✦ Razync IA", key="floating_ai_launcher_btn"):
            st.session_state[_FLOATING_OPEN_KEY] = True
            st.rerun()


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
