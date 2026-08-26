from __future__ import annotations

import streamlit as st


def inject_workspace_style() -> None:
    st.markdown(
        """
        <style>
        .rz-workspace-note {
            padding: .85rem 1rem;
            border: 1px solid var(--rz-border);
            border-radius: 14px;
            background: var(--rz-soft);
            color: var(--rz-muted);
        }

        [data-testid="stAppViewContainer"] .block-container {
            max-width: 1380px;
        }

        /* Login V5 — split-screen premium inspirado no mockup aprovado. */
        .stApp:has(.rz-login-shell) [data-testid="stHeader"] {
            display: none !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stMain"] {
            min-height: 100vh;
            background:
                radial-gradient(circle at 18% 0%, rgba(16,189,242,.08), transparent 34rem),
                linear-gradient(180deg, #edf5f9 0%, #f7fbfd 100%) !important;
        }
        .stApp:has(.rz-login-shell) .block-container {
            max-width: 1240px !important;
            padding: clamp(1rem, 2.7vh, 2rem) 1rem !important;
        }

        .stApp:has(.rz-login-shell)
        .stMainBlockContainer > [data-testid="stVerticalBlock"]:has(.rz-login-shell) {
            display: grid !important;
            grid-template-columns: minmax(0, 1.12fr) minmax(420px, .88fr) !important;
            grid-template-rows: auto auto auto auto 1fr !important;
            column-gap: 0 !important;
            min-height: min(860px, calc(100vh - 2rem)) !important;
            border: 1px solid rgba(128, 158, 178, .28) !important;
            border-radius: 30px !important;
            background: linear-gradient(90deg, #061522 0 55%, #f9fcfe 55% 100%) !important;
            box-shadow: 0 38px 110px rgba(10, 34, 52, .18) !important;
            overflow: hidden !important;
            position: relative !important;
            isolation: isolate !important;
        }
        .stApp:has(.rz-login-shell)
        .stMainBlockContainer > [data-testid="stVerticalBlock"]:has(.rz-login-shell)::before {
            content: "";
            position: absolute;
            inset: 0 45% 0 0;
            z-index: -1;
            pointer-events: none;
            background:
                radial-gradient(circle at 78% 18%, rgba(16,189,242,.18), transparent 12rem),
                radial-gradient(circle at 20% 74%, rgba(28,111,165,.18), transparent 19rem),
                linear-gradient(125deg, transparent 0 55%, rgba(16,189,242,.035) 55% 56%, transparent 56% 100%);
        }
        .stApp:has(.rz-login-shell)
        .stMainBlockContainer > [data-testid="stVerticalBlock"]:has(.rz-login-shell)::after {
            content: "";
            position: absolute;
            left: 8%;
            bottom: 6%;
            width: 38%;
            height: 20%;
            z-index: -1;
            opacity: .45;
            pointer-events: none;
            background:
                linear-gradient(170deg, transparent 0 32%, rgba(16,189,242,.15) 33% 34%, transparent 35% 47%, rgba(16,189,242,.22) 48% 49%, transparent 50%),
                radial-gradient(circle at 15% 70%, rgba(16,189,242,.75) 0 2px, transparent 3px),
                radial-gradient(circle at 43% 56%, rgba(16,189,242,.75) 0 2px, transparent 3px),
                radial-gradient(circle at 71% 36%, rgba(16,189,242,.75) 0 2px, transparent 3px),
                radial-gradient(circle at 92% 20%, rgba(16,189,242,.75) 0 2px, transparent 3px);
            animation: rz-login-float 8s ease-in-out infinite;
        }

        .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(> .stMarkdown > .rz-login-shell) {
            grid-column: 1 !important;
            grid-row: 1 !important;
            align-self: center !important;
            padding: clamp(2.25rem, 4vw, 4.2rem) clamp(2rem, 4vw, 4.3rem) 1.2rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-shell {
            max-width: 520px !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: left !important;
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand {
            display: flex !important;
            align-items: center !important;
            width: fit-content !important;
            gap: .75rem !important;
            margin: 0 0 1.5rem !important;
            padding: 0 !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-mark {
            width: 48px !important;
            height: 48px !important;
            border-radius: 14px !important;
            border: 1px solid rgba(52,200,245,.42) !important;
            box-shadow: 0 12px 34px rgba(16,189,242,.18) !important;
            transition: transform .25s ease, box-shadow .25s ease !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand:hover .rz-login-mark {
            transform: translateY(-2px) rotate(-2deg) !important;
            box-shadow: 0 16px 42px rgba(16,189,242,.28) !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand strong {
            color: #f7fbff !important;
            font-size: 1.55rem !important;
            letter-spacing: -.05em !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-brand span {
            color: #18c7f8 !important;
            font-size: .7rem !important;
            letter-spacing: .06em !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-kicker {
            display: inline-flex !important;
            align-items: center !important;
            width: fit-content !important;
            margin: 0 0 1.2rem !important;
            padding: .48rem .8rem !important;
            border: 1px solid rgba(52,200,245,.28) !important;
            border-radius: 999px !important;
            background: rgba(16,189,242,.08) !important;
            color: #74dcfb !important;
            font-size: .68rem !important;
            font-weight: 800 !important;
            letter-spacing: .045em !important;
            text-transform: uppercase !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-kicker::before {
            content: "";
            width: 7px;
            height: 7px;
            margin-right: .5rem;
            border-radius: 50%;
            background: #43e39e;
            box-shadow: 0 0 0 5px rgba(67,227,158,.08);
        }
        .stApp:has(.rz-login-shell) .rz-login-shell h1 {
            max-width: 510px !important;
            margin: 0 !important;
            color: #f7fbff !important;
            font-size: clamp(2.7rem, 4.4vw, 4.45rem) !important;
            line-height: .98 !important;
            letter-spacing: -.058em !important;
            font-weight: 900 !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-shell h1 em {
            color: #19c4f5 !important;
            font-style: normal !important;
            text-shadow: 0 10px 36px rgba(16,189,242,.16);
        }
        .stApp:has(.rz-login-shell) .rz-login-lead {
            max-width: 480px !important;
            margin: 1.25rem 0 1.55rem !important;
            color: rgba(232,244,251,.72) !important;
            font-size: .98rem !important;
            line-height: 1.7 !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits {
            display: grid !important;
            grid-template-columns: 1fr !important;
            gap: .62rem !important;
            max-width: 455px !important;
            margin: 0 0 1.2rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits span {
            display: flex !important;
            align-items: center !important;
            gap: .78rem !important;
            min-height: 58px !important;
            padding: .8rem 1rem !important;
            border: 1px solid rgba(123,211,241,.18) !important;
            border-radius: 16px !important;
            background: linear-gradient(135deg, rgba(255,255,255,.07), rgba(255,255,255,.035)) !important;
            color: rgba(247,251,255,.94) !important;
            box-shadow: inset 0 1px rgba(255,255,255,.025) !important;
            font-size: .84rem !important;
            font-weight: 760 !important;
            cursor: default !important;
            transition: transform .22s ease, border-color .22s ease, background .22s ease, box-shadow .22s ease !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits span::after {
            content: "→";
            margin-left: auto;
            color: rgba(116,220,251,.72);
            font-size: 1.05rem;
            transition: transform .22s ease, color .22s ease;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits span:hover {
            transform: translateX(6px) !important;
            border-color: rgba(52,200,245,.44) !important;
            background: linear-gradient(135deg, rgba(16,189,242,.14), rgba(255,255,255,.055)) !important;
            box-shadow: 0 14px 32px rgba(0,0,0,.13) !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits span:hover::after {
            transform: translateX(3px);
            color: #75e2ff;
        }
        .stApp:has(.rz-login-shell) .rz-login-benefits b {
            display: inline-grid !important;
            place-items: center !important;
            flex: 0 0 34px !important;
            width: 34px !important;
            height: 34px !important;
            border-radius: 11px !important;
            background: rgba(16,189,242,.12) !important;
            color: #6edcff !important;
            font-size: .65rem !important;
            border: 1px solid rgba(52,200,245,.16);
        }
        .stApp:has(.rz-login-shell) .rz-login-proof {
            display: flex !important;
            flex-wrap: wrap !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: .55rem !important;
            margin: .15rem 0 0 !important;
            color: rgba(226,241,249,.55) !important;
            font-size: .69rem !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-proof span { color: inherit !important; }
        .stApp:has(.rz-login-shell) .rz-login-proof i {
            width: 4px !important;
            height: 4px !important;
            border-radius: 50% !important;
            background: #18c7f8 !important;
        }

        /* Demonstração: CTA discreto e interativo dentro do painel de marketing. */
        .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(button[kind="secondary"]) {
            grid-column: 1 !important;
            grid-row: 2 !important;
            padding: 0 clamp(2rem, 4vw, 4.3rem) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stButton"] {
            max-width: 455px !important;
            margin: .9rem 0 0 !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stButton"] button {
            min-height: 2.8rem !important;
            border: 1px solid rgba(52,200,245,.30) !important;
            border-radius: 14px !important;
            background: rgba(16,189,242,.07) !important;
            color: #dff7ff !important;
            box-shadow: none !important;
            font-size: .76rem !important;
            font-weight: 730 !important;
            transition: transform .2s ease, background .2s ease, border-color .2s ease, box-shadow .2s ease !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stButton"] button:hover {
            transform: translateY(-2px) !important;
            background: rgba(16,189,242,.13) !important;
            border-color: rgba(52,200,245,.52) !important;
            box-shadow: 0 12px 26px rgba(0,0,0,.13) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(.rz-demo-note) {
            grid-column: 1 !important;
            grid-row: 3 !important;
            padding: 0 clamp(2rem, 4vw, 4.3rem) !important;
        }
        .stApp:has(.rz-login-shell) .rz-demo-note {
            max-width: 455px !important;
            margin: .5rem 0 0 !important;
            text-align: left !important;
            color: rgba(226,241,249,.42) !important;
            font-size: .66rem !important;
        }

        /* Card de acesso. */
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] {
            grid-column: 2 !important;
            grid-row: 1 / span 3 !important;
            align-self: center !important;
            justify-self: center !important;
            width: min(88%, 500px) !important;
            max-width: 500px !important;
            margin: 0 !important;
            padding: 1.25rem 1.45rem 1.55rem !important;
            border: 1px solid #d8e5ed !important;
            border-radius: 24px !important;
            background: rgba(255,255,255,.96) !important;
            box-shadow: 0 24px 70px rgba(23,55,76,.12) !important;
            backdrop-filter: blur(18px) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tablist"] {
            gap: .1rem !important;
            margin-bottom: .75rem !important;
            padding: .2rem !important;
            border-radius: 12px !important;
            background: #edf6fa !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] {
            min-height: 2.45rem !important;
            border-radius: 9px !important;
            color: #607487 !important;
            font-size: .73rem !important;
            font-weight: 700 !important;
            transition: background .18s ease, color .18s ease, transform .18s ease !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"]:hover {
            color: #079fce !important;
            transform: translateY(-1px) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
            background: #fff !important;
            color: #087fa7 !important;
            box-shadow: 0 3px 12px rgba(24,71,96,.08) !important;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading {
            position: relative !important;
            padding: 3.1rem .05rem .55rem !important;
            text-align: center !important;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading::before {
            content: "✦";
            position: absolute;
            top: .55rem;
            left: 50%;
            display: grid;
            place-items: center;
            width: 42px;
            height: 42px;
            transform: translateX(-50%);
            border-radius: 50%;
            background: #e7f7fd;
            color: #08b9ef;
            font-size: 1rem;
            box-shadow: 0 10px 30px rgba(8,185,239,.12);
            animation: rz-login-pulse 3.6s ease-in-out infinite;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading strong {
            display: block !important;
            color: #111c27 !important;
            font-size: 1.42rem !important;
            letter-spacing: -.035em !important;
            font-weight: 850 !important;
        }
        .stApp:has(.rz-login-shell) .rz-auth-heading span {
            display: block !important;
            margin-top: .35rem !important;
            color: #6f8292 !important;
            font-size: .78rem !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [data-testid="stForm"] {
            padding: .55rem 0 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTextInput"] label p {
            color: #314657 !important;
            font-size: .72rem !important;
            font-weight: 740 !important;
        }
        .stApp:has(.rz-login-shell) [data-baseweb="input"] {
            min-height: 3.15rem !important;
            border: 1px solid #c7d9e5 !important;
            border-radius: 12px !important;
            background: #fbfdfe !important;
            box-shadow: 0 1px 3px rgba(25,59,78,.03) !important;
            transition: border-color .18s ease, box-shadow .18s ease, background .18s ease !important;
        }
        .stApp:has(.rz-login-shell) [data-baseweb="input"]:focus-within {
            border-color: #08b9ef !important;
            background: #fff !important;
            box-shadow: 0 0 0 4px rgba(8,185,239,.11), 0 8px 20px rgba(33,81,104,.06) !important;
        }
        .stApp:has(.rz-login-shell) input {
            min-height: 3.15rem !important;
            color: #152330 !important;
            font-size: .88rem !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stCheckbox"] p {
            color: #617587 !important;
            font-size: .72rem !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button {
            min-height: 3.1rem !important;
            margin-top: .35rem !important;
            border: 0 !important;
            border-radius: 12px !important;
            background: linear-gradient(90deg, #0878ff 0%, #08b9ef 100%) !important;
            color: #fff !important;
            font-weight: 800 !important;
            box-shadow: 0 12px 30px rgba(8,168,225,.22) !important;
            transition: transform .18s ease, box-shadow .18s ease, filter .18s ease !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-2px) !important;
            filter: saturate(1.08) brightness(1.02) !important;
            box-shadow: 0 16px 36px rgba(8,168,225,.30) !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stLinkButton"] a {
            min-height: 2.85rem !important;
            border: 1px solid #d1e0e9 !important;
            border-radius: 12px !important;
            background: #fff !important;
            color: #263a49 !important;
            box-shadow: none !important;
            transition: transform .18s ease, border-color .18s ease, background .18s ease !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stLinkButton"] a:hover {
            transform: translateY(-1px) !important;
            border-color: #9ccfe0 !important;
            background: #f7fcfe !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] hr {
            border-color: #e0eaf0 !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stTabs"] [data-testid="stCaptionContainer"] {
            color: #8495a2 !important;
            font-size: .67rem !important;
        }

        .stApp:has(.rz-login-shell) [data-testid="stLayoutWrapper"]:has([data-testid="stExpander"]) {
            grid-column: 2 !important;
            grid-row: 4 !important;
            width: min(88%, 500px) !important;
            justify-self: center !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stExpander"] {
            max-width: 500px !important;
            margin: .65rem auto 0 !important;
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(.rz-login-security) {
            grid-column: 2 !important;
            grid-row: 5 !important;
            width: min(88%, 500px) !important;
            justify-self: center !important;
        }
        .stApp:has(.rz-login-shell) .rz-login-security {
            max-width: 500px !important;
            margin: .45rem auto 0 !important;
            text-align: center !important;
            color: #8597a4 !important;
            font-size: .63rem !important;
        }

        @keyframes rz-login-float {
            0%,100% { transform: translate3d(0,0,0); opacity: .38; }
            50% { transform: translate3d(0,-8px,0); opacity: .62; }
        }
        @keyframes rz-login-pulse {
            0%,100% { transform: translateX(-50%) scale(1); box-shadow: 0 10px 30px rgba(8,185,239,.12); }
            50% { transform: translateX(-50%) scale(1.06); box-shadow: 0 12px 34px rgba(8,185,239,.2); }
        }

        /* Tablet: hero acima do login, mantendo linguagem visual. */
        @media (max-width: 980px) {
            .stApp:has(.rz-login-shell) .block-container {
                max-width: 760px !important;
                padding: 1rem .8rem 3rem !important;
            }
            .stApp:has(.rz-login-shell)
            .stMainBlockContainer > [data-testid="stVerticalBlock"]:has(.rz-login-shell) {
                display: block !important;
                min-height: auto !important;
                border-radius: 24px !important;
                background: linear-gradient(180deg, #061522 0 40%, #f9fcfe 40% 100%) !important;
                overflow: hidden !important;
            }
            .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(> .stMarkdown > .rz-login-shell) {
                padding: 2rem 1.5rem .8rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-shell {
                max-width: 620px !important;
                margin: 0 auto !important;
                text-align: center !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-brand,
            .stApp:has(.rz-login-shell) .rz-login-kicker {
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-shell h1 {
                max-width: 620px !important;
                margin: 0 auto !important;
                font-size: clamp(2.25rem, 7vw, 3.4rem) !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-lead {
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-benefits {
                max-width: 560px !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-proof { justify-content: center !important; }
            .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(button[kind="secondary"]),
            .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(.rz-demo-note) {
                padding: 0 1.5rem !important;
            }
            .stApp:has(.rz-login-shell) [data-testid="stButton"] {
                margin: .8rem auto 0 !important;
            }
            .stApp:has(.rz-login-shell) .rz-demo-note {
                margin-left: auto !important;
                margin-right: auto !important;
                text-align: center !important;
            }
            .stApp:has(.rz-login-shell) [data-testid="stTabs"] {
                width: calc(100% - 2rem) !important;
                max-width: 520px !important;
                margin: 2rem auto 0 !important;
            }
        }

        @media (max-width: 600px) {
            [data-testid="stAppViewContainer"] .block-container {
                padding-left: .65rem;
                padding-right: .65rem;
            }
            .stApp:has(.rz-login-shell)
            .stMainBlockContainer > [data-testid="stVerticalBlock"]:has(.rz-login-shell) {
                border-radius: 20px !important;
                background: linear-gradient(180deg, #061522 0 34%, #f9fcfe 34% 100%) !important;
            }
            .stApp:has(.rz-login-shell) [data-testid="stElementContainer"]:has(> .stMarkdown > .rz-login-shell) {
                padding: 1.5rem 1rem .6rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-brand { margin-bottom: 1rem !important; }
            .stApp:has(.rz-login-shell) .rz-login-mark { width: 42px !important; height: 42px !important; }
            .stApp:has(.rz-login-shell) .rz-login-shell h1 { font-size: 2.15rem !important; }
            .stApp:has(.rz-login-shell) .rz-login-lead {
                margin: .9rem auto 1rem !important;
                font-size: .84rem !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-benefits span {
                min-height: 52px !important;
                padding: .68rem .8rem !important;
                border-radius: 13px !important;
            }
            .stApp:has(.rz-login-shell) .rz-login-proof { display: none !important; }
            .stApp:has(.rz-login-shell) [data-testid="stTabs"] {
                width: calc(100% - 1rem) !important;
                margin-top: 1.4rem !important;
                padding: .95rem .85rem 1.15rem !important;
                border-radius: 18px !important;
            }
            .stApp:has(.rz-login-shell) .rz-auth-heading { padding-top: 2.8rem !important; }
            .stApp:has(.rz-login-shell) [data-testid="stTabs"] [role="tab"] p { font-size: .65rem !important; }
            [data-testid="stButton"] button,
            [data-testid="stLinkButton"] a,
            [data-testid="stDownloadButton"] button { min-height: 2.9rem; }
            [data-testid="stMetric"] {
                padding: .72rem .78rem;
                border: 1px solid var(--rz-border);
                border-radius: 12px;
                background: var(--rz-surface);
            }
            [data-testid="stMetricValue"] { font-size: 1.2rem; }
        }

        @media (prefers-reduced-motion: reduce) {
            .stApp:has(.rz-login-shell) *,
            .stApp:has(.rz-login-shell) *::before,
            .stApp:has(.rz-login-shell) *::after {
                animation: none !important;
                transition: none !important;
                scroll-behavior: auto !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
