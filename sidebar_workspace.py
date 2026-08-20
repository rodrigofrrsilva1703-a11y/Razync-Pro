from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from navigation_config import SIDEBAR_GROUPS, SIDEBAR_ICONS, SIDEBAR_LABELS, SIDEBAR_SECONDARY_GROUPS
from onboarding_tools import onboarding_progress


def _render_floating_assistant(page: str, navigate) -> None:
    if page == "Assistente Razync":
        return

    st.markdown(
        """
        <style>
        .st-key-floating_ai_shortcut {
            position: fixed;
            right: 1.35rem;
            bottom: 1.25rem;
            z-index: 100000;
            width: auto !important;
            max-width: min(360px, calc(100vw - 2rem));
        }
        .st-key-floating_ai_shortcut > div {
            width: auto !important;
        }
        .st-key-floating_ai_shortcut [data-testid="stPopover"] > button {
            min-height: 3rem;
            padding: .68rem 1rem;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 38%, var(--rz-border)) !important;
            border-radius: 999px !important;
            color: white !important;
            background: linear-gradient(135deg, var(--rz-primary), #2563eb) !important;
            box-shadow: 0 12px 30px rgba(2, 132, 199, .28) !important;
            font-weight: 700 !important;
        }
        .st-key-floating_ai_shortcut [data-testid="stPopover"] > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 15px 34px rgba(2, 132, 199, .34) !important;
        }
        @media (max-width: 700px) {
            .st-key-floating_ai_shortcut {
                right: .8rem;
                bottom: .8rem;
            }
            .st-key-floating_ai_shortcut [data-testid="stPopover"] > button {
                min-height: 2.72rem;
                padding: .55rem .8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="floating_ai_shortcut"):
        with st.popover("✨ Falar com a IA"):
            st.markdown("**Assistente Razync**")
            st.caption("Pergunte sobre financeiro, DAS, notas, prazos ou o que organizar primeiro.")
            quick_question = st.text_input(
                "Sua pergunta",
                key="floating_ai_question",
                placeholder="Ex.: Como está meu resultado este mês?",
                label_visibility="collapsed",
            )
            if st.button("Perguntar", key="floating_ai_send", type="primary", width="stretch"):
                if quick_question.strip():
                    st.session_state["razync_ai_pending_question"] = quick_question.strip()
                    navigate("Assistente Razync")
                else:
                    st.warning("Digite uma pergunta para continuar.")
            if st.button("Abrir Assistente", key="floating_ai_open", width="stretch"):
                navigate("Assistente Razync")


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

    _render_floating_assistant(page, navigate)
