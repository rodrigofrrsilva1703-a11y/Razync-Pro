from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from command_center import render_command_center
from navigation_config import SIDEBAR_ICONS, SIDEBAR_LABELS
from onboarding_tools import onboarding_progress


_FLOATING_OPEN_KEY = "razync_floating_open"


def _apply_appearance_choice() -> None:
    st.session_state["ui_theme"] = st.session_state["appearance_select_v2"]


def _floating_chat_shell_styles() -> None:
    st.markdown(
        """
        <style>
        .st-key-floating_ai_v7_shell {
            position: fixed !important;
            right: .8rem !important;
            bottom: .8rem !important;
            z-index: 999995 !important;
            width: min(370px, calc(100vw - 1.1rem)) !important;
            height: 550px !important;
            max-height: calc(100vh - 1.1rem) !important;
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
            .st-key-floating_ai_v7_shell {
                right: .4rem !important;
                bottom: .4rem !important;
                width: calc(100vw - .8rem) !important;
                height: min(520px, calc(100vh - .8rem)) !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_floating_assistant(page: str, user: dict, navigate) -> None:
    if page == "Assistente Razync":
        st.session_state[_FLOATING_OPEN_KEY] = True
        navigate("Dashboard")
        return

    _floating_chat_shell_styles()
    is_open = bool(st.session_state.get(_FLOATING_OPEN_KEY, False))
    if is_open:
        from floating_ai_bridge import process_pending_floating_question
        from floating_chat_v7_host import render_isolated_chat_v7

        process_pending_floating_question(user=user, page=page)

        def floating_navigate(destination: str) -> None:
            if destination == "Assistente Razync":
                st.session_state[_FLOATING_OPEN_KEY] = True
                st.rerun()
                return
            navigate(destination)

        with st.container(key="floating_ai_v7_shell"):
            render_isolated_chat_v7(user=user, page=page, navigate=floating_navigate)
        return

    with st.container(key="floating_ai_launcher"):
        if st.button("✦ Razync IA", key="floating_ai_launcher_btn"):
            st.session_state[_FLOATING_OPEN_KEY] = True
            st.rerun()


def _nav_button(destination: str, page: str, navigate, *, key_prefix: str = "main") -> None:
    if st.button(
        SIDEBAR_LABELS[destination],
        key=f"{key_prefix}_nav_{destination}",
        icon=SIDEBAR_ICONS.get(destination),
        disabled=page == destination,
        width="stretch",
    ):
        navigate(destination)


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
) -> None:
    business_name = profile.get("trade_name") or profile.get("business_name") or "Seu MEI"

    with st.sidebar:
        st.markdown(
            f"""
            <div class="rz-side-brand">
              <img src="{brand_logo_data_uri}" alt="Razync Pro">
              <div>
                <strong>Razync<em>PRO</em></strong>
                <span>{escape(str(business_name))}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="sidebar_navigation"):
            st.caption("WORKSPACE")
            for destination in (
                "Dashboard",
                "Financeiro",
                "Fiscal",
                "Documentos",
                "Clientes e Fornecedores",
            ):
                _nav_button(destination, page, navigate)

            with st.expander("Ferramentas", expanded=page in {"Produtividade", "Conta e Sistema"}):
                _nav_button("Produtividade", page, navigate, key_prefix="tools")
                _nav_button("Conta e Sistema", page, navigate, key_prefix="tools")

            with st.expander("Buscar função"):
                render_command_center(
                    navigate=navigate,
                    current_page=page,
                    documents=documents,
                )

            setup = onboarding_progress(
                profile,
                not transactions.empty,
                bool(das_rows),
                bool(documents),
            )
            if setup["percent"] < 100:
                st.caption("CONFIGURAÇÃO")
                if st.button(
                    f"Primeiros passos · {setup['percent']}%",
                    key="sidebar_onboarding",
                    icon=":material/checklist:",
                    disabled=page == "Primeiros Passos",
                    width="stretch",
                ):
                    navigate("Primeiros Passos")

        st.divider()
        with st.expander("Preferências"):
            st.selectbox(
                "Aparência",
                ["Claro", "Escuro"],
                index=1 if st.session_state.get("ui_theme") == "Escuro" else 0,
                key="appearance_select_v2",
                on_change=_apply_appearance_choice,
            )
            if st.button(
                "Atualizar dados",
                key="sidebar_refresh",
                icon=":material/refresh:",
                width="stretch",
            ):
                refresh_data()

    _render_floating_assistant(page, user, navigate)
