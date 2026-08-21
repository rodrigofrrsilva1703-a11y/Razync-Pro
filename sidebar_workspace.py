from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from floating_assistant import render_floating_assistant
from floating_chat_theme import inject_floating_assistant_styles
from navigation_config import SIDEBAR_GROUPS, SIDEBAR_ICONS, SIDEBAR_LABELS, SIDEBAR_SECONDARY_GROUPS
from onboarding_tools import onboarding_progress


_FLOATING_OPEN_KEY = "razync_floating_open"


def _render_floating_assistant(page: str, user: dict, navigate) -> None:
    if page == "Assistente Razync":
        return

    is_open = bool(st.session_state.get(_FLOATING_OPEN_KEY, False))
    if is_open:
        with st.container(key="floating_ai_panel"):
            render_floating_assistant(user=user, page=page, navigate=navigate)
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
    inject_floating_assistant_styles()

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
