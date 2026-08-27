from __future__ import annotations

import re
from html import escape
from datetime import date
from time import monotonic
from typing import Callable

import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from ai_assistant import RazyncAIError, ask_razync_ai, build_safe_business_context
from assistant_actions import AssistantActionError, plan_document_action
from assistant_action_store import AssistantActionStoreError, list_actions
from assistant_operational_tools import answer_record_search, plan_record_operation, proactive_answer
from assistant_state_store import (
    AssistantStateStoreError, list_pending_drafts, save_draft, save_feedback, set_draft_status,
)
from assistant_audio import AssistantAudioError, transcribe_audio
from assistant_automation_service import (
    confirm_automation as execute_assistant_action,
    prepare_automation as plan_assistant_action,
    revise_automation as revise_action_draft,
    undo_automation as undo_assistant_action,
)
from assistant_history import (
    AssistantHistoryError, WELCOME_MESSAGE, append_exchange as persist_ai_exchange,
    append_message as persist_ai_message,
    create_conversation, get_or_create_conversation, list_conversations,
    load_messages, serialize_timestamp,
)
from ai_provider_router import ProviderChainError, run_provider_chain
from ai_usage_store import AIUsageStoreError, get_ai_usage, release_ai_request, reserve_ai_request
from assistant_query_engine import analyze_business_question
from assistant_resources import build_product_context, build_resource_bundle, should_prepare_resources
from fiscal_rules import annual_limit_for
from document_intelligence import analyze_document
from gemini_provider import DEFAULT_GEMINI_MODEL, GeminiAIError, ask_razync_gemini, diagnose_gemini
from product_core import assistant_answer, supports_instant_assistant_answer
from monitoring import safe_error


DEFAULT_UI_MODEL = "gpt-5.4-mini"
DEFAULT_DAILY_REQUEST_LIMIT = 20
AI_USAGE_CACHE_SECONDS = 30.0
_SAFE_API_META = re.compile(r"^[A-Za-z0-9_.:\-/]{1,96}$")

SUGGESTED_QUESTIONS = [
    "Analisar meu negócio",
    "Registrar uma despesa",
    "Registrar uma receita",
    "Cadastrar uma nota",
    "Ver minhas prioridades",
    "Gerar relatório financeiro",
    "Criar uma despesa mensal",
    "Criar um lembrete",
    "Cadastrar um cliente",
]

FLOATING_QUICK_ACTIONS = (
    ("− Despesa", "Registrar uma despesa"),
    ("+ Receita", "Registrar uma receita"),
    ("▤ Nota", "Cadastrar uma nota"),
)

SUGGESTED_ACTIONS = (
    ("Analisar", "Analisar meu negócio"),
    ("Prioridades", "Ver minhas prioridades"),
    ("Relatório", "Gerar relatório financeiro"),
    ("Nova despesa", "Registrar uma despesa"),
    ("Nova receita", "Registrar uma receita"),
    ("Cadastrar nota", "Cadastrar uma nota"),
    ("Despesa mensal", "Criar uma despesa mensal"),
    ("Criar lembrete", "Criar um lembrete"),
    ("Novo cliente", "Cadastrar um cliente"),
)


def _dynamic_suggestions(
    *, mode: str, profile: dict, transactions: pd.DataFrame, das_rows: list[dict],
    obligations: list[dict], documents: list[dict], annual_limit: float, current_year: int,
) -> list[tuple[str, str]]:
    """Prioritize useful prompts from the user's current business state."""
    if mode == "Fazer":
        suggestions = [
            ("Registrar despesa", "Registrar uma despesa"),
            ("Registrar receita", "Registrar uma receita"),
            ("Criar lembrete", "Criar um lembrete"),
            ("Despesa mensal", "Criar uma despesa mensal"),
            ("Cadastrar nota", "Cadastrar uma nota"),
            ("Novo cliente", "Cadastrar um cliente"),
        ]
        if not profile.get("cnpj") or not profile.get("main_activity"):
            suggestions.insert(0, ("Completar meu MEI", "Quero completar os dados essenciais do meu MEI"))
        if not documents:
            suggestions.insert(1, ("Organizar documentos", "Quero analisar e organizar um documento"))
        return suggestions[:6]

    suggestions = [
        ("Minhas prioridades", "Verifique tudo e mostre minhas prioridades"),
        ("Relatório do mês", "Gere um relatório das minhas receitas e despesas deste mês"),
        ("Faturamento", "Gere um relatório do meu faturamento mensal deste ano"),
        ("Clientes", "Gere um relatório dos meus clientes deste ano"),
        ("Analisar negócio", "Analise meu negócio e indique riscos e próximas ações"),
        ("Resumo do mês", "Resuma minhas receitas, despesas e resultado deste mês"),
        ("Limite do MEI", f"Quanto do limite anual de {annual_limit:.2f} já usei em {current_year}?"),
        ("Despesas", "Quais despesas mais pesam e o que devo revisar?"),
        ("Documentos", "Quais lançamentos estão sem documento?"),
    ]
    if das_rows:
        suggestions.insert(0, ("Revisar DAS", "Revise meus DAS e destaque atrasos ou próximos vencimentos"))
    if obligations:
        suggestions.insert(1, ("Obrigações", "Quais obrigações estão vencidas ou próximas?"))
    if transactions.empty:
        suggestions = [
            ("Começar agora", "O que preciso configurar primeiro no Razync?"),
            ("Como registrar", "Como registrar minha primeira movimentação?"),
            ("Organizar MEI", "Crie um roteiro simples para organizar meu MEI"),
        ] + suggestions
    return suggestions[:6]


def _pending_overview(
    *, profile: dict, transactions: pd.DataFrame, das_rows: list[dict], obligations: list[dict],
    documents: list[dict], current_year: int,
) -> list[tuple[str, str, str]]:
    """Return a compact deterministic approval-safe work queue."""
    def is_overdue(value) -> bool:
        if not value:
            return False
        try:
            parsed = pd.to_datetime(value, errors="coerce")
            return not pd.isna(parsed) and parsed.date() < date.today()
        except (TypeError, ValueError, OverflowError):
            return False

    items: list[tuple[str, str, str]] = []
    if not profile.get("cnpj") or not profile.get("main_activity"):
        items.append(("Cadastro do MEI", "Dados essenciais ainda incompletos", "Quero completar os dados do meu MEI"))
    overdue_das = [row for row in das_rows if str(row.get("status") or "").lower() not in {"pago", "concluído"} and is_overdue(row.get("due_date"))]
    if overdue_das:
        items.append(("DAS", f"{len(overdue_das)} competência(s) possivelmente em atraso", "Revise meus DAS em atraso e diga o que fazer"))
    overdue_obligations = [row for row in obligations if str(row.get("status") or "") != "Concluído" and is_overdue(row.get("due_date"))]
    if overdue_obligations:
        items.append(("Obrigações", f"{len(overdue_obligations)} obrigação(ões) vencida(s)", "Revise minhas obrigações vencidas"))
    if not transactions.empty and "document_number" in transactions.columns:
        missing_docs = int(transactions["document_number"].fillna("").astype(str).str.strip().eq("").sum())
        if missing_docs:
            items.append(("Documentos", f"{missing_docs} lançamento(s) sem documento informado", "Mostre os lançamentos sem documento"))
    if not documents:
        items.append(("Arquivos", "Nenhum documento armazenado", "Como devo organizar os documentos do meu MEI?"))
    return items[:5]


def _trace_caption(result: dict, *, current_year: int, elapsed: float) -> str:
    provider = str(result.get("provider") or "Local")
    model = str(result.get("model") or "Razync local")
    return f"Fonte: {provider} · Motor: {model} · Dados da conta: {current_year} · {elapsed:.1f}s"


def _inject_assistant_style() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) {
            width: min(460px, calc(100vw - 1.25rem)); max-height: min(760px, calc(100vh - 4.75rem));
            padding: 0 !important; overflow-x: hidden; overflow-y: auto;
            scrollbar-width: thin; scrollbar-color: var(--rz-border) transparent;
            border: 1px solid color-mix(in srgb, var(--rz-primary) 28%, var(--rz-border));
            border-radius: 22px; background: var(--rz-surface);
            box-shadow: 0 28px 80px rgba(2,27,43,.24), 0 5px 18px rgba(2,27,43,.08);
        }
        [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) > div { padding: 0 .95rem .9rem !important; }
        .rz-ai-shell-marker { display: none; }
        .rz-ai-head {
            position: sticky; top: 0; z-index: 5; display: flex; align-items: center; gap: .78rem;
            padding: .9rem .05rem .78rem; margin-bottom: .72rem; border-bottom: 1px solid var(--rz-border);
            background: color-mix(in srgb, var(--rz-surface) 94%, transparent); backdrop-filter: blur(14px);
        }
        .rz-ai-head-icon, .rz-ai-page-icon {
            display: grid; place-items: center; color: #fff; font-weight: 900; letter-spacing: -.04em;
            background: linear-gradient(145deg, #081927 5%, var(--rz-primary) 72%, #29d4ff);
            box-shadow: 0 10px 26px color-mix(in srgb, var(--rz-primary) 28%, transparent);
        }
        .rz-ai-head-icon { width: 44px; height: 44px; flex: 0 0 44px; border-radius: 14px; font-size: 1rem; }
        .rz-ai-head-copy { min-width: 0; flex: 1; }
        .rz-ai-head strong { display: block; color: var(--rz-text); font-size: 1rem; letter-spacing: -.02em; }
        .rz-ai-head span { display: flex; align-items: center; gap: .4rem; color: var(--rz-muted); font-size: .72rem; margin-top: .13rem; }
        .rz-ai-head-badge { padding: .28rem .48rem; border-radius: 999px; color: var(--rz-primary); background: var(--rz-primary-soft); font-size: .62rem; font-weight: 800; letter-spacing: .04em; }
        .rz-ai-online { width: 7px; height: 7px; border-radius: 50%; background: #18a66a; box-shadow: 0 0 0 3px rgba(24,166,106,.12); }
        .rz-ai-examples { color: var(--rz-muted); font-size: .72rem; line-height: 1.5; margin: -.15rem .12rem .68rem; }
        .rz-ai-safety { display: flex; align-items: center; gap: .4rem; color: var(--rz-muted); font-size: .67rem; padding: .72rem .12rem .08rem; border-top: 1px solid var(--rz-border); margin-top: .72rem; }
        .st-key-floating_ai_quick_actions { margin: -.1rem 0 .62rem; }
        .st-key-floating_ai_quick_actions [data-testid="stButton"] button,
        .st-key-full_ai_quick_actions [data-testid="stButton"] button {
            border-color: var(--rz-border); background: var(--rz-surface); color: var(--rz-text);
            font-weight: 700; box-shadow: 0 3px 12px rgba(2,27,43,.035); transition: .16s ease;
        }
        .st-key-floating_ai_quick_actions [data-testid="stButton"] button { min-height: 2.15rem; padding: .34rem .35rem; border-radius: 10px; background: var(--rz-soft); font-size: .7rem; }
        .st-key-floating_ai_quick_actions [data-testid="stButton"] button:hover,
        .st-key-full_ai_quick_actions [data-testid="stButton"] button:hover { border-color: var(--rz-primary); color: var(--rz-primary); background: var(--rz-primary-soft); transform: translateY(-1px); }
        .st-key-floating_ai_messages { max-height: min(320px, 38vh) !important; padding: .08rem .14rem .36rem !important; scrollbar-width: thin; scrollbar-color: var(--rz-border) transparent; }
        .st-key-floating_ai_messages [data-testid="stChatMessage"] { border: 1px solid var(--rz-border); border-radius: 16px; padding: .66rem .74rem; margin: .46rem 0; background: var(--rz-soft); box-shadow: 0 3px 12px rgba(2,27,43,.035); }
        .st-key-floating_ai_messages [aria-label="Chat message from user"] { margin-left: 2.6rem; background: linear-gradient(135deg, var(--rz-primary-soft), color-mix(in srgb, var(--rz-primary-soft) 76%, var(--rz-surface))); border-color: color-mix(in srgb, var(--rz-primary) 26%, var(--rz-border)); }
        .st-key-floating_ai_messages [aria-label="Chat message from assistant"] { margin-right: 1.35rem; }
        .st-key-floating_ai_messages [data-testid="stChatMessageAvatarUser"], .st-key-floating_ai_messages [data-testid="stChatMessageAvatarAssistant"] { transform: scale(.78); transform-origin: top center; }
        .st-key-floating_ai_messages [data-testid="stMarkdownContainer"] p { font-size: .82rem; line-height: 1.55; }
        .st-key-floating_ai_composer { margin-top: .45rem; }
        .st-key-floating_ai_composer [data-testid="stChatInput"], .st-key-full_ai_composer [data-testid="stChatInput"] { border: 1px solid var(--rz-border); border-radius: 15px; background: var(--rz-surface); box-shadow: 0 7px 22px rgba(2,27,43,.06); overflow: hidden; }
        .st-key-floating_ai_composer [data-testid="stChatInput"] > div, .st-key-floating_ai_composer [data-testid="stChatInput"] textarea, .st-key-full_ai_composer [data-testid="stChatInput"] > div, .st-key-full_ai_composer [data-testid="stChatInput"] textarea { background: var(--rz-surface) !important; color: var(--rz-text) !important; }
        .st-key-floating_ai_composer [data-testid="stChatInput"]:focus-within, .st-key-full_ai_composer [data-testid="stChatInput"]:focus-within { border-color: var(--rz-primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--rz-primary) 14%, transparent); }
        .st-key-floating_ai_composer [data-testid="stChatInput"] textarea { min-height: 2.9rem !important; font-size: .82rem !important; }
        .st-key-floating_ai_composer [data-testid="stChatInputSubmitButton"], .st-key-full_ai_composer [data-testid="stChatInputSubmitButton"] { color: #fff !important; background: var(--rz-primary) !important; border-radius: 10px !important; }
        .rz-ai-page-intro { position: relative; overflow: hidden; display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1.3rem 1.4rem; margin: .1rem 0 1rem; border: 1px solid color-mix(in srgb, var(--rz-primary) 22%, var(--rz-border)); border-radius: 20px; background: linear-gradient(125deg, var(--rz-surface) 5%, var(--rz-primary-soft) 100%); box-shadow: 0 12px 34px rgba(2,27,43,.07); }
        .rz-ai-page-intro::after { content: ""; position: absolute; width: 180px; height: 180px; right: -55px; top: -90px; border-radius: 50%; background: color-mix(in srgb, var(--rz-primary) 13%, transparent); }
        .rz-ai-page-title { display: flex; align-items: center; gap: .9rem; position: relative; z-index: 1; }
        .rz-ai-page-icon { width: 48px; height: 48px; border-radius: 15px; }
        .rz-ai-page-intro strong { display: block; font-size: 1.18rem; color: var(--rz-text); letter-spacing: -.025em; }
        .rz-ai-page-intro span { color: var(--rz-muted); font-size: .8rem; }
        .rz-ai-page-status { position: relative; z-index: 1; display: flex; align-items: center; gap: .45rem; padding: .45rem .68rem; border-radius: 999px; background: var(--rz-surface); border: 1px solid var(--rz-border); color: var(--rz-text); font-size: .7rem; font-weight: 700; }
        .st-key-full_ai_toolbar { border: 1px solid var(--rz-border); border-radius: 15px; padding: .72rem .82rem .25rem; background: var(--rz-surface); margin-bottom: .8rem; }
        .rz-ai-provider-line { display: flex; align-items: center; gap: .55rem; color: var(--rz-text); font-size: .78rem; font-weight: 720; }
        .rz-ai-provider-line small { color: var(--rz-muted); font-size: .69rem; font-weight: 500; }
        .rz-ai-provider-dot { width: 8px; height: 8px; border-radius: 50%; background: #18a66a; box-shadow: 0 0 0 4px rgba(24,166,106,.1); }
        .st-key-full_ai_messages { min-height: 230px; max-height: min(540px, 56vh); overflow-y: auto; padding: 1rem 1.05rem !important; margin: .2rem 0 .85rem; border: 1px solid var(--rz-border); border-radius: 20px; background: linear-gradient(180deg, var(--rz-soft), var(--rz-surface)); scrollbar-width: thin; scrollbar-color: var(--rz-border) transparent; }
        .st-key-full_ai_messages [data-testid="stChatMessage"] { width: min(86%, 760px); padding: .8rem .9rem; margin: .55rem 0; border: 1px solid var(--rz-border); border-radius: 17px; background: var(--rz-surface); box-shadow: 0 4px 16px rgba(2,27,43,.04); }
        .st-key-full_ai_messages [aria-label="Chat message from user"] { margin-left: auto; background: var(--rz-primary-soft); border-color: color-mix(in srgb, var(--rz-primary) 28%, var(--rz-border)); }
        .st-key-full_ai_messages [aria-label="Chat message from assistant"] { margin-right: auto; }
        .st-key-full_ai_messages [data-testid="stMarkdownContainer"] p { line-height: 1.62; }
        .rz-ai-quick-title { margin: .25rem 0 .42rem; color: var(--rz-muted); font-size: .7rem; font-weight: 760; letter-spacing: .04em; text-transform: uppercase; }
        .st-key-full_ai_quick_actions [data-testid="stButton"] button { min-height: 2.55rem; border-radius: 12px; font-size: .76rem; }
        .st-key-full_ai_composer { margin: .72rem 0 .3rem; }
        .st-key-full_ai_composer [data-testid="stChatInput"] textarea { min-height: 3.15rem !important; }
        .rz-ai-composer-help { color: var(--rz-muted); font-size: .68rem; text-align: center; margin: .2rem 0 .75rem; }
        .rz-ai-mode-help { color: var(--rz-muted); font-size: .72rem; margin: -.2rem 0 .65rem; }
        .rz-ai-trace { color: var(--rz-muted); font-size: .68rem; padding: .5rem .7rem; margin: -.4rem 0 .75rem; border-left: 3px solid var(--rz-primary); background: var(--rz-soft); border-radius: 0 9px 9px 0; }
        .rz-ai-memory-note { color: var(--rz-muted); font-size: .74rem; line-height: 1.55; }

        /* Conversa minimalista: estrutura inspirada em mensageiros móveis. */
        [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) {
            width: min(410px, calc(100vw - .8rem)); max-height: min(690px, calc(100vh - 4.25rem));
            border-radius: 14px; border-color: var(--rz-border); box-shadow: 0 18px 52px rgba(2,27,43,.2);
        }
        [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) > div { padding: 0 !important; }
        .rz-ai-head { margin: 0; padding: .72rem .85rem; border: 0; gap: .65rem; background: linear-gradient(135deg, #071a2a, #0a607c); backdrop-filter: none; }
        .rz-ai-head-icon { width: 38px; height: 38px; flex-basis: 38px; border-radius: 50%; font-size: .82rem; background: var(--rz-primary); box-shadow: none; }
        .rz-ai-head strong { color: #fff; font-size: .94rem; }
        .rz-ai-head span { color: rgba(255,255,255,.76); font-size: .68rem; margin-top: .06rem; }
        .rz-ai-head-badge, .rz-ai-examples, .st-key-floating_ai_quick_actions { display: none !important; }
        .st-key-floating_ai_messages { min-height: 310px; max-height: min(430px, 48vh) !important; margin: 0 !important; padding: .72rem .7rem !important; background-color: var(--rz-soft); background-image: radial-gradient(color-mix(in srgb, var(--rz-muted) 10%, transparent) .7px, transparent .7px); background-size: 13px 13px; }
        .st-key-floating_ai_messages [data-testid="stChatMessage"], .st-key-full_ai_messages [data-testid="stChatMessage"] { width: fit-content; max-width: 84%; min-width: 3.2rem; border: 0; border-radius: 11px; padding: .48rem .62rem; margin: .34rem 0; background: var(--rz-surface); box-shadow: 0 1px 2px rgba(2,27,43,.12); }
        .st-key-floating_ai_messages [aria-label="Chat message from user"], .st-key-full_ai_messages [aria-label="Chat message from user"] { margin-left: auto; margin-right: 0; background: color-mix(in srgb, var(--rz-primary-soft) 86%, var(--rz-surface)); }
        .st-key-floating_ai_messages [aria-label="Chat message from assistant"], .st-key-full_ai_messages [aria-label="Chat message from assistant"] { margin-left: 0; margin-right: auto; }
        .st-key-floating_ai_messages [data-testid="stChatMessageAvatarUser"], .st-key-floating_ai_messages [data-testid="stChatMessageAvatarAssistant"], .st-key-full_ai_messages [data-testid="stChatMessageAvatarUser"], .st-key-full_ai_messages [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
        .st-key-floating_ai_messages [data-testid="stMarkdownContainer"] p { font-size: .8rem; line-height: 1.46; }
        .st-key-floating_ai_composer { margin: 0; padding: .55rem .62rem; background: var(--rz-surface); border-top: 1px solid var(--rz-border); }
        .st-key-floating_ai_composer [data-testid="stChatInput"] { border-radius: 999px; background: var(--rz-soft); box-shadow: none; }
        .st-key-floating_ai_composer [data-testid="stChatInput"] > div, .st-key-floating_ai_composer [data-testid="stChatInput"] textarea { background: var(--rz-soft) !important; }
        .st-key-floating_ai_composer [data-testid="stChatInputSubmitButton"] { border-radius: 50% !important; }
        .rz-ai-safety { justify-content: center; margin: 0; padding: .42rem .6rem .5rem; border: 0; background: var(--rz-surface); font-size: .61rem; }
        .st-key-full_ai_messages { background-color: var(--rz-soft); background-image: radial-gradient(color-mix(in srgb, var(--rz-muted) 9%, transparent) .7px, transparent .7px); background-size: 13px 13px; border-radius: 14px; }
        .rz-ai-page-intro { padding: .8rem 1rem; border-radius: 14px; background: var(--rz-surface); box-shadow: none; }
        .rz-ai-page-intro::after { display: none; }
        @media (max-width: 700px) {
            [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) { width: calc(100vw - .75rem); max-height: calc(100vh - 4rem); border-radius: 18px; }
            [data-testid="stPopoverBody"]:has(.rz-ai-shell-marker) > div { padding: 0 .72rem .72rem !important; }
            .st-key-floating_ai_messages { max-height: 34vh !important; }
            .st-key-floating_ai_messages [aria-label="Chat message from user"] { margin-left: 1rem; }
            .st-key-floating_ai_messages [aria-label="Chat message from assistant"] { margin-right: .5rem; }
            .rz-ai-head-badge { display: none; }
            .rz-ai-page-intro { align-items: flex-start; flex-direction: column; padding: 1.05rem; }
            .rz-ai-page-status { align-self: flex-start; }
            .st-key-full_ai_messages { padding: .72rem !important; min-height: 190px; max-height: 52vh; border-radius: 16px; }
            .st-key-full_ai_messages [data-testid="stChatMessage"] { width: 96%; padding: .7rem .75rem; }
            .st-key-full_ai_quick_actions [data-testid="stButton"] button { min-height: 2.35rem; padding: .3rem .4rem; font-size: .69rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_assistant_header(*, compact: bool) -> None:
    if compact:
        st.markdown(
            """
            <span class="rz-ai-shell-marker"></span>
            <div class="rz-ai-head">
              <div class="rz-ai-head-icon">RZ</div>
              <div class="rz-ai-head-copy"><strong>Razync</strong><span><i class="rz-ai-online"></i>online</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="rz-ai-page-intro">
              <div class="rz-ai-page-title">
                <div class="rz-ai-page-icon">RZ</div>
                <div><strong>Assistente Razync</strong><span>Analise, organize e execute tarefas com confirmação.</span></div>
              </div>
              <div class="rz-ai-page-status"><i class="rz-ai-online"></i> Disponível agora</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "")
    except Exception:
        return ""


def _daily_request_limit() -> int:
    raw = _secret("OPENAI_DAILY_REQUEST_LIMIT")
    try:
        return max(1, int(raw)) if raw else DEFAULT_DAILY_REQUEST_LIMIT
    except (TypeError, ValueError):
        return DEFAULT_DAILY_REQUEST_LIMIT


def _current_user_id() -> int | None:
    user = st.session_state.get("user")
    if not isinstance(user, dict):
        return None
    try:
        user_id = int(user.get("id"))
    except (TypeError, ValueError):
        return None
    return user_id if user_id > 0 else None


def _remember_ai_usage(user_id: int, count: int) -> None:
    st.session_state[f"razync_ai_usage_{int(user_id)}"] = {
        "count": max(0, int(count)),
        "expires_at": monotonic() + AI_USAGE_CACHE_SECONDS,
    }


def _cached_ai_usage(user_id: int, *, force: bool = False) -> int:
    key = f"razync_ai_usage_{int(user_id)}"
    cached = st.session_state.get(key)
    if not force and isinstance(cached, dict):
        try:
            if float(cached.get("expires_at") or 0) > monotonic():
                return max(0, int(cached.get("count") or 0))
        except (TypeError, ValueError):
            pass
    count = get_ai_usage(user_id)
    _remember_ai_usage(user_id, count)
    return count


def _invalidate_session_snapshot(user_id: int) -> None:
    st.session_state.pop(f"_mei_snapshot_{int(user_id)}", None)
    st.session_state.pop(f"_mei_snapshot_version_{int(user_id)}", None)


def _safe_api_status_metadata(exc: APIStatusError) -> str:
    labels = (("parâmetro", "param"), ("tipo", "type"), ("código", "code"))
    parts: list[str] = []
    for label, attr in labels:
        raw = getattr(exc, attr, None)
        if raw is None:
            continue
        value = str(raw).strip()
        if value and _SAFE_API_META.fullmatch(value):
            parts.append(f"{label}: {value}")
    return " · ".join(parts)


def _diagnose_openai(api_key: str, model: str) -> tuple[bool, str]:
    if not api_key.strip():
        return False, "OPENAI_API_KEY não foi encontrada nos Secrets do Streamlit."

    try:
        client = OpenAI(api_key=api_key.strip(), timeout=15.0, max_retries=0)
        response = client.responses.create(
            model=model.strip() or DEFAULT_UI_MODEL,
            input="Responda somente com OK.",
            store=False,
        )
        if not (response.output_text or "").strip():
            return False, "A OpenAI respondeu, mas não retornou texto. Tente novamente."
        return True, f"Conexão com a OpenAI funcionando. Modelo validado: {model}."
    except AuthenticationError:
        return False, "A chave da OpenAI foi recusada. Gere uma nova API key e atualize OPENAI_API_KEY nos Secrets."
    except RateLimitError:
        return False, "A API recusou a chamada por limite de uso ou crédito. Verifique Billing/Usage do projeto da OpenAI."
    except APITimeoutError:
        return False, "A conexão com a OpenAI excedeu o tempo limite. Tente novamente em alguns instantes."
    except APIConnectionError:
        return False, "O Streamlit não conseguiu alcançar a OpenAI. Verifique a conexão e tente novamente."
    except APIStatusError as exc:
        status = int(getattr(exc, "status_code", 0) or 0)
        if status == 403:
            return False, f"A chave não tem permissão para usar o modelo {model}. Troque OPENAI_MODEL ou revise o projeto da API."
        if status == 404:
            return False, f"O modelo {model} não está disponível para esta chave. Use OPENAI_MODEL = \"{DEFAULT_UI_MODEL}\"."
        if status == 400:
            details = _safe_api_status_metadata(exc)
            if details:
                return False, f"A OpenAI rejeitou um parâmetro da chamada ({details})."
            return False, "A OpenAI rejeitou a configuração da chamada, mas não informou um parâmetro seguro para exibir."
        return False, f"A OpenAI respondeu com erro HTTP {status or 'desconhecido'}. Revise a configuração da API."
    except Exception:
        return False, "Não foi possível validar a IA agora. A análise local do Razync continua disponível."


_diagnose_ai = _diagnose_openai


def _provider_state() -> dict:
    gemini_api_key = _secret("GEMINI_API_KEY")
    gemini_model = _secret("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    openai_api_key = _secret("OPENAI_API_KEY")
    openai_model = _secret("OPENAI_MODEL") or DEFAULT_UI_MODEL
    gemini_enabled = bool(gemini_api_key.strip())
    openai_enabled = bool(openai_api_key.strip())
    providers = [name for name, enabled in (("Gemini", gemini_enabled), ("OpenAI", openai_enabled)) if enabled]
    models = [model for model, enabled in ((gemini_model, gemini_enabled), (openai_model, openai_enabled)) if enabled]
    return {
        "gemini_api_key": gemini_api_key,
        "gemini_model": gemini_model,
        "openai_api_key": openai_api_key,
        "openai_model": openai_model,
        "gemini_enabled": gemini_enabled,
        "openai_enabled": openai_enabled,
        "ai_enabled": bool(providers),
        "provider": " → ".join(providers) if providers else "Local",
        "model": " → ".join(models) if models else "Razync local",
        "fallback_enabled": len(providers) > 1,
    }


def _ensure_messages() -> list[dict]:
    """Load one owned conversation per session and gracefully fall back to memory."""
    user_id = _current_user_id()
    loaded_for = st.session_state.get("razync_ai_history_loaded_for")
    if "razync_ai_messages" in st.session_state and loaded_for == user_id:
        return st.session_state["razync_ai_messages"]

    messages: list[dict] = []
    if user_id is not None:
        try:
            current_id = st.session_state.get("razync_ai_conversation_id")
            conversation_id = get_or_create_conversation(user_id, int(current_id) if current_id else None)
            st.session_state["razync_ai_conversation_id"] = conversation_id
            messages = load_messages(user_id, conversation_id)
        except (AssistantHistoryError, TypeError, ValueError):
            st.session_state["razync_ai_history_warning"] = (
                "O histórico persistente está temporariamente indisponível. Esta conversa continuará nesta sessão."
            )

    if not messages:
        messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
    st.session_state["razync_ai_messages"] = messages
    st.session_state["razync_ai_history_loaded_for"] = user_id
    return messages


def _append_message(role: str, content: str, *, metadata: dict | None = None) -> None:
    safe_content = str(content or "").strip()
    if not safe_content:
        return
    messages = _ensure_messages()
    messages.append({"role": role, "content": safe_content})
    user_id = _current_user_id()
    conversation_id = st.session_state.get("razync_ai_conversation_id")
    if user_id is None or not conversation_id:
        return
    try:
        persist_ai_message(user_id, int(conversation_id), role, safe_content, metadata=metadata)
    except AssistantHistoryError:
        st.session_state["razync_ai_history_warning"] = (
            "Não foi possível sincronizar uma mensagem com o histórico. Ela continua visível nesta sessão."
        )


def _activate_conversation(conversation_id: int) -> None:
    st.session_state["razync_ai_conversation_id"] = int(conversation_id)
    st.session_state.pop("razync_ai_messages", None)
    st.session_state.pop("razync_ai_history_loaded_for", None)
    st.session_state.pop("razync_ai_last_resources", None)
    st.session_state.pop("razync_ai_last_trace", None)
    st.session_state.pop("razync_ai_pending_action", None)


def _start_new_conversation() -> None:
    user_id = _current_user_id()
    if user_id is not None:
        try:
            st.session_state["razync_ai_conversation_id"] = create_conversation(user_id)
        except AssistantHistoryError:
            st.session_state.pop("razync_ai_conversation_id", None)
            st.session_state["razync_ai_history_warning"] = "A nova conversa ficará somente nesta sessão por enquanto."
    st.session_state.pop("razync_ai_messages", None)
    st.session_state.pop("razync_ai_history_loaded_for", None)
    st.session_state.pop("razync_ai_last_resources", None)
    st.session_state.pop("razync_ai_last_resource_question", None)
    st.session_state.pop("razync_ai_last_trace", None)
    st.session_state.pop("razync_ai_pending_action", None)
    st.session_state.pop("razync_ai_last_receipt", None)


def _opening_date(profile: dict) -> date | None:
    value = profile.get("opening_date")
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _session_snapshot(user_id: int) -> tuple[dict, pd.DataFrame, pd.DataFrame, list[dict], list[dict], list[dict], float, int] | None:
    snapshot = st.session_state.get(f"_mei_snapshot_{user_id}")
    if not isinstance(snapshot, dict):
        return None
    profile = dict(snapshot.get("profile") or {})
    transactions = pd.DataFrame(snapshot.get("transactions") or [])
    if transactions.empty:
        transactions = pd.DataFrame(columns=[
            "id", "tx_date", "tx_type", "description", "category", "value", "document_number", "counterparty", "payment_method"
        ])
    else:
        transactions["tx_date"] = pd.to_datetime(transactions["tx_date"], errors="coerce")
    invoices = pd.DataFrame(snapshot.get("invoices") or [])
    if not invoices.empty and "issue_date" in invoices.columns:
        invoices["issue_date"] = pd.to_datetime(invoices["issue_date"], errors="coerce")
    das_rows = list(snapshot.get("das") or [])
    obligations = list(snapshot.get("obligations") or [])
    documents = list(snapshot.get("documents") or [])
    current_year = date.today().year
    annual_limit = annual_limit_for(_opening_date(profile), current_year, profile.get("annual_limit"))
    return profile, transactions, invoices, das_rows, obligations, documents, annual_limit, current_year


def _fallback_answer(
    question: str,
    *,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    annual_limit: float,
    current_year: int,
    fallback_answer: Callable[[str], str] | None,
) -> str:
    if fallback_answer is not None:
        return fallback_answer(question)
    return assistant_answer(
        question,
        transactions,
        invoices,
        das_rows,
        annual_limit,
        current_year,
        obligations=obligations,
        documents=documents,
    )


def _answer_question(
    question: str,
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    annual_limit: float,
    current_year: int,
    current_page: str | None,
    fallback_answer: Callable[[str], str] | None = None,
) -> dict:
    provider = _provider_state()
    provider_used = "Local"
    user_id = _current_user_id()
    daily_limit = _daily_request_limit()
    quota_ready = bool(user_id)
    notices: list[tuple[str, str]] = []
    usage_count = 0

    pending_action = st.session_state.get("razync_ai_pending_action")
    action_question = question
    if isinstance(pending_action, dict) and pending_action.get("missing_fields"):
        original_request = str(pending_action.get("original_request") or "").strip()
        if original_request:
            action_question = f"{original_request}. Informação adicional: {question}"

    try:
        action_draft = plan_record_operation(
            action_question,
            transactions=transactions,
            invoices=invoices,
            obligations=obligations,
        )
        if action_draft is None:
            action_draft = plan_assistant_action(action_question)
    except Exception as exc:
        safe_error("assistant_action_planning_failed", exc, feature="assistant", operation="plan_action")
        action_draft = None

    if action_draft is not None:
        action_state = action_draft.to_dict()
        action_state["original_request"] = action_question
        st.session_state["razync_ai_pending_action"] = action_state
        if user_id is not None:
            try:
                save_draft(user_id, action_state, conversation_id=st.session_state.get("razync_ai_conversation_id"))
            except AssistantStateStoreError:
                notices.append(("warning", "A prévia está segura nesta sessão, mas a central de aprovações não sincronizou agora."))
        if action_draft.ready:
            answer = "Pronto — preparei a ação. Confira o resumo e confirme para salvar."
        else:
            missing = ", ".join(action_draft.missing_fields)
            answer = f"Só preciso de: {missing}. Responda aqui ou complete os campos da ação."
        return {
            "answer": answer,
            "notices": notices,
            "provider": action_draft.source,
            "model": "Razync local",
            "action": action_state,
        }

    search_result = answer_record_search(
        question,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
    )
    if search_result is not None:
        return {
            "answer": search_result["answer"] + f"\n\n_Confiança {search_result['confidence']} · {search_result['reason']}_",
            "notices": [], "provider": "Busca local", "model": "Razync local",
        }

    if any(term in question.lower() for term in ("prioridades", "o que preciso fazer", "pendências", "pendencias", "verifique tudo")):
        proactive = proactive_answer(
            transactions=transactions, invoices=invoices, obligations=obligations, das_rows=das_rows,
        )
        return {
            "answer": proactive["answer"] + f"\n\n_Confiança {proactive['confidence']} · {proactive['reason']}_",
            "notices": [], "provider": "Análise proativa", "model": "Razync local",
        }

    instant_query = analyze_business_question(question, transactions, default_year=current_year)
    if instant_query.handled:
        return {
            "answer": instant_query.summary,
            "notices": [], "provider": "Análise instantânea", "model": "Razync local",
        }

    if supports_instant_assistant_answer(question):
        return {
            "answer": _fallback_answer(
                question,
                transactions=transactions,
                invoices=invoices,
                das_rows=das_rows,
                obligations=obligations,
                documents=documents,
                annual_limit=annual_limit,
                current_year=current_year,
                fallback_answer=fallback_answer,
            ),
            "notices": [], "provider": "Análise instantânea", "model": "Razync local",
        }

    if quota_ready and user_id is not None:
        try:
            usage_count = _cached_ai_usage(user_id)
        except AIUsageStoreError:
            quota_ready = False

    prior_conversation = list(_ensure_messages()[-6:])
    local_answer = lambda: _fallback_answer(
        question,
        transactions=transactions,
        invoices=invoices,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        annual_limit=annual_limit,
        current_year=current_year,
        fallback_answer=fallback_answer,
    )

    if provider["ai_enabled"] and quota_ready and user_id is not None:
        try:
            allowed, reserved_count = reserve_ai_request(user_id, daily_limit)
        except AIUsageStoreError:
            allowed = False
            reserved_count = usage_count
            notices.append(("warning", "O controle diário da IA não respondeu. Usei a análise local do Razync."))
        else:
            _remember_ai_usage(user_id, reserved_count)

        if allowed:
            context = build_safe_business_context(
                profile=profile,
                transactions=transactions,
                invoices=invoices,
                das_rows=das_rows,
                obligations=obligations,
                documents=documents,
                annual_limit=annual_limit,
                year=current_year,
            )
            context["razync_product"] = build_product_context(documents, current_page=current_page)
            attempts = []
            if provider["gemini_enabled"]:
                attempts.append((
                    "Gemini",
                    lambda: ask_razync_gemini(
                        question,
                        context=context,
                        api_key=provider["gemini_api_key"],
                        model=provider["gemini_model"],
                        conversation=prior_conversation,
                    ),
                ))
            if provider["openai_enabled"]:
                attempts.append((
                    "OpenAI",
                    lambda: ask_razync_ai(
                        question,
                        context=context,
                        api_key=provider["openai_api_key"],
                        model=provider["openai_model"],
                        conversation=prior_conversation,
                    ),
                ))
            try:
                answer, provider_used, failed_providers = run_provider_chain(attempts)
                if failed_providers:
                    notices.append((
                        "info",
                        f"{' e '.join(failed_providers)} não respondeu. O {provider_used} assumiu automaticamente.",
                    ))
            except ProviderChainError as exc:
                try:
                    released_count = release_ai_request(user_id)
                    _remember_ai_usage(user_id, released_count)
                except AIUsageStoreError:
                    pass
                answer = local_answer()
                provider_used = "Local"
                attempted = " e ".join(exc.attempted_providers)
                if attempted:
                    notices.append(("warning", f"{attempted} não respondeu. Usei a análise local do Razync."))
                else:
                    notices.append(("warning", "A IA externa não respondeu agora. Usei a análise local do Razync."))
        else:
            answer = local_answer()
            if reserved_count >= daily_limit:
                notices.append(("warning", f"A quota diária de {daily_limit} respostas externas foi atingida. Usei a análise local."))
            else:
                notices.append(("warning", "Não foi possível reservar o uso da IA agora. Usei a análise local."))
    else:
        answer = local_answer()
        if provider["ai_enabled"] and not quota_ready:
            notices.append(("warning", "O controle de quota está indisponível. Usei a análise local do Razync."))

    return {
        "answer": answer,
        "notices": notices,
        "provider": provider_used,
        "model": provider["model"],
    }


def _prepare_resources(
    question: str,
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    current_year: int,
) -> dict:
    if not should_prepare_resources(question):
        return {"route": None, "route_label": None, "downloads": [], "note": None}
    user_id = _current_user_id()
    if user_id is None:
        return {"route": None, "route_label": None, "downloads": [], "note": None}
    try:
        return build_resource_bundle(
            question,
            user_id=user_id,
            profile=profile,
            transactions=transactions,
            invoices=invoices,
            das_rows=das_rows,
            obligations=obligations,
            documents=documents,
            year=current_year,
            access_token=str(st.session_state.get("access_token") or ""),
            refresh_token=str(st.session_state.get("refresh_token") or ""),
        )
    except Exception as exc:
        safe_error("assistant_resources_failed", exc, feature="assistant", operation="prepare_resources")
        return {
            "route": None,
            "route_label": None,
            "downloads": [],
            "note": "Não consegui preparar os recursos do sistema agora, mas a conversa continua disponível.",
        }


def _render_notices(notices: list[tuple[str, str]]) -> None:
    for level, text in notices:
        if level == "error":
            st.error(text)
        elif level == "warning":
            st.warning(text)
        else:
            st.info(text)


def _render_resources(bundle: dict | None, *, key_prefix: str, current_page: str | None = None, navigate=None) -> None:
    if not bundle:
        return
    note = bundle.get("note")
    if note:
        st.info(note)
    downloads = list(bundle.get("downloads") or [])
    if downloads:
        st.caption("Arquivos preparados pelo Razync")
        for idx, asset in enumerate(downloads):
            st.download_button(
                str(asset.get("label") or "Baixar arquivo"),
                asset.get("data") or b"",
                file_name=str(asset.get("file_name") or "arquivo"),
                mime=str(asset.get("mime") or "application/octet-stream"),
                key=f"{key_prefix}_download_{idx}",
                width="stretch",
            )
    route = bundle.get("route")
    route_label = bundle.get("route_label")
    if route and route != current_page:
        if st.button(str(route_label or f"Abrir {route}"), key=f"{key_prefix}_route", width="stretch"):
            if navigate is not None:
                navigate(route)
            else:
                st.session_state["_navigate_to"] = route
                st.rerun()


def _render_pending_action(*, key_prefix: str) -> None:
    draft = st.session_state.get("razync_ai_pending_action")
    if not isinstance(draft, dict):
        return

    with st.container(border=True):
        st.markdown("**Ação preparada pela IA**")
        st.write(str(draft.get("summary") or "Confira os dados antes de continuar."))
        missing = list(draft.get("missing_fields") or [])
        if missing:
            st.warning("Falta informar: " + ", ".join(str(item) for item in missing) + ".")

        action_type = str(draft.get("action_type") or "")
        payload = dict(draft.get("payload") or {})
        with st.expander("Revisar ou corrigir dados", expanded=bool(missing)):
            with st.form(f"{key_prefix}_edit_form"):
                updates: dict = {}
                if action_type in {"transaction", "recurring_transaction"}:
                    updates["tx_type"] = st.selectbox(
                        "Tipo", ["Receita", "Despesa"],
                        index=0 if payload.get("tx_type") == "Receita" else 1,
                        key=f"{key_prefix}_tx_type",
                    )
                    updates["description"] = st.text_input("Descrição", value=str(payload.get("description") or ""), key=f"{key_prefix}_description")
                    updates["value"] = st.number_input("Valor", min_value=0.0, value=float(payload.get("value") or 0), step=10.0, key=f"{key_prefix}_value")
                    updates["category"] = st.text_input("Categoria", value=str(payload.get("category") or "Outros"), key=f"{key_prefix}_category")
                    updates["payment_method"] = st.selectbox(
                        "Pagamento", ["PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro"],
                        index=["PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro"].index(payload.get("payment_method")) if payload.get("payment_method") in ["PIX", "Dinheiro", "Cartão", "Boleto", "Transferência", "Outro"] else 5,
                        key=f"{key_prefix}_payment",
                    )
                    date_key = "tx_date" if action_type == "transaction" else "next_date"
                    updates[date_key] = st.text_input("Data (AAAA-MM-DD)", value=str(payload.get(date_key) or ""), key=f"{key_prefix}_date")
                    if action_type == "recurring_transaction":
                        frequencies = ["Semanal", "Mensal", "Anual"]
                        updates["frequency"] = st.selectbox("Frequência", frequencies, index=frequencies.index(payload.get("frequency")) if payload.get("frequency") in frequencies else 1, key=f"{key_prefix}_frequency")
                elif action_type == "invoice":
                    updates["number"] = st.text_input("Número da nota", value=str(payload.get("number") or ""), key=f"{key_prefix}_number")
                    updates["customer"] = st.text_input("Cliente", value=str(payload.get("customer") or ""), key=f"{key_prefix}_customer")
                    updates["description"] = st.text_input("Descrição", value=str(payload.get("description") or ""), key=f"{key_prefix}_description")
                    updates["amount"] = st.number_input("Valor", min_value=0.0, value=float(payload.get("amount") or 0), step=10.0, key=f"{key_prefix}_amount")
                    updates["issue_date"] = st.text_input("Data (AAAA-MM-DD)", value=str(payload.get("issue_date") or ""), key=f"{key_prefix}_date")
                elif action_type == "obligation":
                    updates["title"] = st.text_input("Lembrete", value=str(payload.get("title") or ""), key=f"{key_prefix}_title")
                    updates["due_date"] = st.text_input("Vencimento (AAAA-MM-DD)", value=str(payload.get("due_date") or ""), key=f"{key_prefix}_date")
                    updates["category"] = st.text_input("Categoria", value=str(payload.get("category") or "Administrativo"), key=f"{key_prefix}_category")
                    updates["notes"] = st.text_area("Observações", value=str(payload.get("notes") or ""), key=f"{key_prefix}_notes")
                elif action_type == "contact":
                    contact_types = ["Cliente", "Fornecedor", "Contato"]
                    updates["contact_type"] = st.selectbox("Tipo", contact_types, index=contact_types.index(payload.get("contact_type")) if payload.get("contact_type") in contact_types else 2, key=f"{key_prefix}_contact_type")
                    updates["name"] = st.text_input("Nome", value=str(payload.get("name") or ""), key=f"{key_prefix}_name")
                    updates["document"] = st.text_input("CPF ou CNPJ", value=str(payload.get("document") or ""), key=f"{key_prefix}_document")
                    updates["email"] = st.text_input("E-mail", value=str(payload.get("email") or ""), key=f"{key_prefix}_email")
                    updates["phone"] = st.text_input("Telefone", value=str(payload.get("phone") or ""), key=f"{key_prefix}_phone")
                editable = action_type in {"transaction", "recurring_transaction", "invoice", "obligation", "contact"}
                if not editable:
                    st.caption("Esta ação foi vinculada a um registro específico. Para mudar o alvo, cancele e faça um novo pedido.")
                reviewed = st.form_submit_button("Atualizar prévia", width="stretch", disabled=not editable)
            if reviewed:
                try:
                    revised = revise_action_draft(draft, updates)
                except AssistantActionError as exc:
                    st.error(str(exc))
                else:
                    revised_state = revised.to_dict()
                    revised_state["original_request"] = draft.get("original_request", "")
                    st.session_state["razync_ai_pending_action"] = revised_state
                    user_id = _current_user_id()
                    if user_id is not None:
                        try:
                            save_draft(user_id, revised_state, conversation_id=st.session_state.get("razync_ai_conversation_id"))
                        except AssistantStateStoreError:
                            pass
                    st.rerun()

        st.caption("O Razync só grava depois da sua confirmação. Pagamentos e emissões oficiais nunca são executados aqui.")
        confirm, cancel = st.columns(2)
        if confirm.button("Confirmar e salvar", key=f"{key_prefix}_confirm", type="primary", width="stretch", disabled=bool(missing)):
            user_id = _current_user_id()
            if user_id is None:
                st.error("Sua sessão expirou. Entre novamente para salvar.")
                return
            try:
                with st.spinner("Salvando com segurança..."):
                    receipt = execute_assistant_action(user_id, draft, return_receipt=True)
            except AssistantActionError as exc:
                st.error(str(exc))
                return
            message = str(receipt.get("message") or "Ação concluída.")
            st.session_state["razync_ai_last_receipt"] = receipt
            st.session_state.pop("razync_ai_pending_action", None)
            st.session_state.pop("razync_ai_last_resources", None)
            try:
                set_draft_status(user_id, str(draft.get("action_key") or ""), "confirmed")
            except AssistantStateStoreError:
                pass
            _invalidate_session_snapshot(user_id)
            _append_message("assistant", message, metadata={"event": "action_confirmed"})
            st.success(message)
            st.rerun()
        if cancel.button("Cancelar", key=f"{key_prefix}_cancel", width="stretch"):
            st.session_state.pop("razync_ai_pending_action", None)
            user_id = _current_user_id()
            if user_id is not None:
                try:
                    set_draft_status(user_id, str(draft.get("action_key") or ""), "cancelled")
                except AssistantStateStoreError:
                    pass
            _append_message("assistant", "Ação cancelada. Nenhum dado foi alterado.", metadata={"event": "action_cancelled"})
            st.rerun()


def _render_last_action_undo(*, key_prefix: str) -> None:
    receipt = st.session_state.get("razync_ai_last_receipt")
    if not isinstance(receipt, dict):
        return
    with st.container(border=True):
        st.caption("Última alteração feita pela IA nesta sessão")
        if st.button("Desfazer última ação", key=f"{key_prefix}_undo", width="stretch"):
            user_id = _current_user_id()
            if user_id is None:
                st.error("Sua sessão expirou. Entre novamente.")
                return
            try:
                message = undo_assistant_action(user_id, receipt)
            except AssistantActionError as exc:
                st.error(str(exc))
                return
            st.session_state.pop("razync_ai_last_receipt", None)
            _invalidate_session_snapshot(user_id)
            _append_message("assistant", message, metadata={"event": "action_undone"})
            st.success(message)
            st.rerun()


def _render_document_intake(*, key_prefix: str) -> None:
    with st.expander("Ler nota, comprovante ou DAS"):
        uploaded_files = st.file_uploader(
            "Envie PDFs ou fotos para a IA preparar os dados",
            type=["pdf", "png", "jpg", "jpeg", "webp"], key=f"{key_prefix}_document_upload",
            accept_multiple_files=True,
            help="A leitura e o OCR são feitos localmente. Nada é salvo sem sua confirmação.",
        )
        if uploaded_files and st.button("Analisar documentos", key=f"{key_prefix}_analyze_document", width="stretch"):
            drafts: list[dict] = []
            analyses: list[dict] = []
            for uploaded in list(uploaded_files)[:10]:
                try:
                    analysis = analyze_document(uploaded.getvalue(), uploaded.type or "application/pdf", uploaded.name)
                    draft = plan_document_action(analysis, uploaded.name)
                except Exception as exc:
                    safe_error("assistant_document_analysis_failed", exc, feature="assistant", operation="document_ocr")
                    analyses.append({"filename": uploaded.name, "confidence": "Falha"})
                    continue
                analyses.append({"filename": uploaded.name, **analysis})
                if draft is not None:
                    drafts.append(draft.to_dict())
            if not drafts:
                st.info("Os arquivos foram lidos, mas faltaram dados para preparar ações. Envie imagens mais nítidas ou complete os dados manualmente.")
                return
            if len(drafts) == 1:
                state = drafts[0]
            else:
                from uuid import uuid4
                total = sum(float(item.get("payload", {}).get("value") or item.get("payload", {}).get("amount") or 0) for item in drafts)
                state = {
                    "action_type": "batch", "payload": {"items": drafts}, "missing_fields": [], "ready": True,
                    "summary": f"{len(drafts)} ações extraídas de documentos · total identificado de R$ {total:,.2f}",
                    "source": "Documentos", "action_key": uuid4().hex, "channel": "web",
                }
            state["original_request"] = f"{len(uploaded_files)} documento(s) enviado(s)"
            st.session_state["razync_ai_pending_action"] = state
            st.session_state["razync_ai_document_analysis"] = analyses
            user_id = _current_user_id()
            if user_id is not None:
                try:
                    save_draft(user_id, state, conversation_id=st.session_state.get("razync_ai_conversation_id"))
                except AssistantStateStoreError:
                    pass
            confidence = "Alta" if all(item.get("confidence") == "Alta" for item in analyses) else "Média" if any(item.get("confidence") in {"Alta", "Média"} for item in analyses) else "Baixa"
            st.success(f"{len(drafts)} ação(ões) preparada(s) · confiança geral {confidence}. Confira antes de salvar.")
            st.rerun()

    with st.expander("Enviar áudio"):
        st.caption("O áudio é enviado à OpenAI somente para transcrição e exige confirmação antes de qualquer lançamento.")
        audio = st.file_uploader(
            "Envie ou grave um áudio com seu pedido",
            type=["mp3", "m4a", "ogg", "wav", "webm", "mp4"],
            key=f"{key_prefix}_audio_upload",
            help="Exemplo: Gastei 80 reais de combustível hoje.",
        )
        if audio is not None and st.button("Transcrever e enviar", key=f"{key_prefix}_transcribe_audio", width="stretch"):
            provider = _provider_state()
            try:
                with st.spinner("Transcrevendo áudio..."):
                    transcript = transcribe_audio(
                        audio.getvalue(), audio.name,
                        api_key=str(provider.get("openai_api_key") or ""),
                    )
            except AssistantAudioError as exc:
                st.error(str(exc))
                return
            st.session_state["razync_ai_pending_question"] = transcript
            st.rerun()


def _render_action_history(user_id: int | None) -> None:
    with st.expander("Ações realizadas pela IA"):
        if user_id is None:
            st.caption("Entre novamente para acessar o histórico.")
            return
        try:
            actions = list_actions(user_id, limit=12)
        except AssistantActionStoreError as exc:
            st.warning(str(exc))
            return
        if not actions:
            st.caption("Nenhuma ação confirmada pela IA ainda.")
            return
        status_labels = {
            "completed": "Concluída", "undone": "Desfeita",
            "failed": "Falhou", "processing": "Processando",
        }
        for item in actions:
            status = status_labels.get(str(item.get("status") or ""), "Registrada")
            channel = "WhatsApp" if item.get("channel") == "whatsapp" else "Site"
            st.markdown(f"**{status}** · {channel}")
            st.caption(str(item.get("summary") or "Ação da IA"))


def _render_approval_center(user_id: int | None) -> None:
    if user_id is None:
        return
    with st.expander("Central de aprovações"):
        try:
            drafts = list_pending_drafts(user_id, limit=20)
        except AssistantStateStoreError as exc:
            st.warning(str(exc))
            return
        if not drafts:
            st.caption("Nenhuma ação aguardando sua confirmação.")
            return
        st.caption(f"{len(drafts)} ação(ões) aguardando revisão. Nada é gravado antes da confirmação.")
        current_key = str((st.session_state.get("razync_ai_pending_action") or {}).get("action_key") or "")
        for index, draft in enumerate(drafts):
            left, right = st.columns([4, 1])
            left.markdown(f"**{draft.get('summary') or 'Ação preparada'}**")
            left.caption("WhatsApp" if draft.get("channel") == "whatsapp" else "Site")
            if right.button(
                "Revisar" if str(draft.get("action_key")) != current_key else "Aberta",
                key=f"ai_approval_open_{index}_{draft.get('action_key')}",
                disabled=str(draft.get("action_key")) == current_key,
                width="stretch",
            ):
                st.session_state["razync_ai_pending_action"] = draft
                st.rerun()


def _render_last_answer_feedback(user_id: int | None, messages: list[dict]) -> None:
    if user_id is None:
        return
    last = next((message for message in reversed(messages) if message.get("role") == "assistant"), None)
    if not last or str(last.get("content") or "") == WELCOME_MESSAGE:
        return
    content = str(last.get("content") or "")
    st.caption("Esta resposta resolveu?")
    yes, no, spacer = st.columns([1, 1, 5])
    if yes.button("Sim", key="razync_ai_feedback_yes", width="stretch"):
        try:
            save_feedback(user_id, content, True, conversation_id=st.session_state.get("razync_ai_conversation_id"))
            st.toast("Obrigado. Avaliação registrada.")
        except AssistantStateStoreError as exc:
            st.warning(str(exc))
    if no.button("Não", key="razync_ai_feedback_no", width="stretch"):
        try:
            save_feedback(user_id, content, False, conversation_id=st.session_state.get("razync_ai_conversation_id"))
            st.toast("Obrigado. Vamos usar isso para melhorar a IA.")
        except AssistantStateStoreError as exc:
            st.warning(str(exc))


def _store_turn(question: str, answer: str, resources: dict | None = None) -> None:
    safe_question = str(question or "").strip()
    safe_answer = str(answer or "").strip()
    if not safe_question or not safe_answer:
        return
    messages = _ensure_messages()
    messages.extend([
        {"role": "user", "content": safe_question},
        {"role": "assistant", "content": safe_answer},
    ])
    user_id = _current_user_id()
    conversation_id = st.session_state.get("razync_ai_conversation_id")
    if user_id is not None and conversation_id:
        try:
            persist_ai_exchange(
                user_id,
                int(conversation_id),
                safe_question,
                safe_answer,
                assistant_metadata={"resources": bool(resources)},
            )
        except AssistantHistoryError:
            st.session_state["razync_ai_history_warning"] = (
                "Não foi possível sincronizar esta conversa com o histórico. Ela continua visível nesta sessão."
            )
    st.session_state["razync_ai_last_resources"] = resources or {}
    st.session_state["razync_ai_last_resource_question"] = question


def _provider_caption(result: dict) -> str:
    provider = str(result.get("provider") or "Local")
    if provider == "Local":
        return "Resposta processada pelo mecanismo seguro local do Razync."
    return f"Resposta processada por {provider}."


def _chat_avatar(role: str) -> str:
    return ":material/person:" if role == "user" else ":material/auto_awesome:"


def render_floating_ai_assistant(*, user: dict, page: str, navigate) -> None:
    _inject_assistant_style()
    try:
        user_id = int(user.get("id"))
    except (TypeError, ValueError):
        return
    snapshot = _session_snapshot(user_id)
    if snapshot is None:
        st.caption("O copiloto ficará disponível após os dados do Razync carregarem.")
        return
    profile, transactions, invoices, das_rows, obligations, documents, annual_limit, current_year = snapshot
    messages = _ensure_messages()

    _render_assistant_header(compact=True)

    with st.container(key="floating_ai_messages"):
        for message in messages[-6:]:
            with st.chat_message(message["role"], avatar=_chat_avatar(message["role"])):
                st.markdown(message["content"])

    with st.container(key="floating_ai_composer"):
        typed_question = st.chat_input("Mensagem", key="floating_ai_chat_input")
    question = typed_question

    if question and question.strip():
        question = question.strip()
        with st.spinner("Pensando..."):
            result = _answer_question(
                question,
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
                question,
                profile=profile,
                transactions=transactions,
                invoices=invoices,
                das_rows=das_rows,
                obligations=obligations,
                documents=documents,
                current_year=current_year,
            )
        _store_turn(question, result["answer"], resources)
        st.session_state["razync_ai_flash_notices"] = result["notices"]
        st.rerun()

    _render_notices(st.session_state.pop("razync_ai_flash_notices", []))
    _render_resources(
        st.session_state.get("razync_ai_last_resources"),
        key_prefix="floating_ai",
        current_page=page,
        navigate=navigate,
    )
    _render_pending_action(key_prefix="floating_ai_action")
    _render_last_action_undo(key_prefix="floating_ai")
    st.markdown('<div class="rz-ai-safety">As alterações só são salvas com sua confirmação.</div>', unsafe_allow_html=True)


def _render_conversation_controls(user_id: int | None) -> None:
    left, right = st.columns([1, 1])
    if left.button("Nova conversa", key="razync_ai_new_chat", icon=":material/edit_square:", width="stretch"):
        _start_new_conversation()
        st.rerun()

    with right.popover("Conversas", icon=":material/history:", width="stretch"):
        if user_id is None:
            st.caption("Entre novamente para acessar o histórico.")
            return
        try:
            conversations = list_conversations(user_id, limit=12)
        except AssistantHistoryError as exc:
            st.warning(str(exc))
            return
        if not conversations:
            st.caption("Nenhuma conversa anterior.")
            return
        current_id = st.session_state.get("razync_ai_conversation_id")
        for conversation in conversations:
            title = str(conversation.get("title") or "Conversa")
            timestamp = serialize_timestamp(conversation.get("updated_at"))
            label = f"{title}\n{timestamp}" if timestamp else title
            if st.button(
                label,
                key=f"ai_conversation_{conversation['id']}",
                type="primary" if int(conversation["id"]) == int(current_id or 0) else "secondary",
                width="stretch",
            ):
                _activate_conversation(int(conversation["id"]))
                st.rerun()


def _render_ai_settings(provider: dict, *, quota_ready: bool, usage_count: int, daily_limit: int) -> None:
    with st.expander("Configurações e diagnóstico"):
        if provider["ai_enabled"] and quota_ready:
            st.caption(f"{provider['provider']} · {provider['model']} · {usage_count}/{daily_limit} respostas hoje")
        elif provider["ai_enabled"]:
            st.caption("IA externa configurada; o controle de uso está temporariamente indisponível.")
        else:
            st.caption("Modo local ativo. Configure GEMINI_API_KEY ou OPENAI_API_KEY para respostas avançadas.")
        st.caption("Documentos e OCR são processados localmente; áudios são enviados à OpenAI para transcrição. Toda ação exige confirmação.")
        if st.button("Testar conexão da IA", key="razync_ai_diagnostic", width="stretch"):
            with st.spinner("Testando conexão..."):
                if provider["gemini_enabled"]:
                    ok, diagnosis = diagnose_gemini(provider["gemini_api_key"], provider["gemini_model"])
                elif provider["openai_enabled"]:
                    ok, diagnosis = _diagnose_openai(provider["openai_api_key"], provider["openai_model"])
                else:
                    ok, diagnosis = False, "Nenhuma API externa foi configurada."
            (st.success if ok else st.error)(diagnosis)


def render_ai_assistant(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    annual_limit: float,
    current_year: int,
    fallback_answer: Callable[[str], str],
) -> None:
    _inject_assistant_style()
    provider = _provider_state()
    user_id = _current_user_id()
    daily_limit = _daily_request_limit()
    quota_ready = bool(user_id)
    usage_count = 0
    if quota_ready:
        try:
            usage_count = _cached_ai_usage(user_id)
        except AIUsageStoreError:
            quota_ready = False

    _render_conversation_controls(user_id)
    history_warning = st.session_state.pop("razync_ai_history_warning", None)
    if history_warning:
        st.warning(history_warning)

    mode = st.radio(
        "Como você quer usar o Razync?",
        ["Perguntar", "Fazer"],
        horizontal=True,
        key="razync_ai_mode",
        help="Perguntar analisa e explica. Fazer prepara uma ação e sempre pede confirmação antes de salvar.",
    )
    st.markdown(
        '<div class="rz-ai-mode-help">'
        + ("Analise números, riscos e prioridades com base nos dados cadastrados." if mode == "Perguntar" else "Prepare cadastros e tarefas. Você revisa tudo antes de confirmar.")
        + "</div>",
        unsafe_allow_html=True,
    )

    pending_items = _pending_overview(
        profile=profile,
        transactions=transactions,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        current_year=current_year,
    )
    pending_prompt = None
    with st.expander(f"Central de pendências · {len(pending_items)} item(ns)", expanded=bool(pending_items)):
        if not pending_items:
            st.success("Nenhuma pendência automática importante encontrada agora.")
        for idx, (title, detail, prompt) in enumerate(pending_items):
            row, action = st.columns([4, 1.2])
            row.markdown(f"**{title}**")
            row.caption(detail)
            if action.button("Analisar", key=f"ai_pending_overview_{idx}", width="stretch"):
                pending_prompt = prompt

    suggested = None
    suggestions = _dynamic_suggestions(
        mode=mode,
        profile=profile,
        transactions=transactions,
        das_rows=das_rows,
        obligations=obligations,
        documents=documents,
        annual_limit=annual_limit,
        current_year=current_year,
    )
    with st.expander("Sugestões para agora", expanded=not bool(st.session_state.get("razync_ai_messages"))):
        with st.container(key="full_ai_quick_actions"):
            cols = st.columns(3)
            for idx, (label, prompt) in enumerate(suggestions):
                if cols[idx % 3].button(label, key=f"ai_suggestion_{idx}", width="stretch"):
                    suggested = prompt

    messages = _ensure_messages()
    with st.container(key="full_ai_messages"):
        for message in messages[-100:]:
            with st.chat_message(message["role"], avatar=_chat_avatar(message["role"])):
                st.markdown(message["content"])
    _render_last_answer_feedback(user_id, messages)

    last_trace = st.session_state.get("razync_ai_last_trace")
    if last_trace:
        st.markdown(f'<div class="rz-ai-trace">{escape(str(last_trace))}</div>', unsafe_allow_html=True)

    with st.expander("Contexto e memória usados"):
        st.markdown(
            f'<div class="rz-ai-memory-note">Área atual: <strong>Assistente Razync</strong><br>'
            f'Contexto recente: até 6 mensagens desta conversa<br>'
            f'Dados disponíveis: {len(transactions)} movimentações, {len(invoices)} notas, '
            f'{len(das_rows)} DAS, {len(obligations)} obrigações e {len(documents)} documentos.<br>'
            'Documentos brutos, credenciais e identificadores diretos não são enviados ao provedor externo.</div>',
            unsafe_allow_html=True,
        )

    pending_context = st.session_state.pop("razync_ai_pending_context", None)
    if isinstance(pending_context, dict) and pending_context.get("source") == "dashboard_insight":
        st.info(
            f"Contexto recebido do painel: **{pending_context.get('title', 'Insight')}** — "
            f"{pending_context.get('detail', '')}"
        )
    pending_question = st.session_state.pop("razync_ai_pending_question", None)
    with st.container(key="full_ai_composer"):
        typed_question = st.chat_input(
            "Pergunte sobre seu MEI..." if mode == "Perguntar" else "Descreva a ação que deseja preparar...",
            key="full_ai_chat_input",
        )
    st.markdown('<div class="rz-ai-composer-help">Enter para enviar · as alterações só são salvas com sua confirmação</div>', unsafe_allow_html=True)
    incoming_question = pending_prompt or suggested or pending_question or typed_question
    _render_notices(st.session_state.pop("razync_ai_flash_notices", []))
    if incoming_question and not st.session_state.get("razync_ai_processing_question"):
        incoming_question = str(incoming_question).strip()
        if incoming_question:
            _append_message("user", incoming_question)
            st.session_state["razync_ai_processing_question"] = incoming_question
            st.rerun()

    question = st.session_state.pop("razync_ai_processing_question", None)
    if not question:
        _render_resources(
            st.session_state.get("razync_ai_last_resources"),
            key_prefix="full_ai_idle",
            current_page="Assistente Razync",
        )
        _render_pending_action(key_prefix="full_ai_idle_action")
        _render_approval_center(user_id)
        _render_document_intake(key_prefix="full_ai_idle")
        _render_last_action_undo(key_prefix="full_ai_idle")
        _render_action_history(user_id)
        _render_ai_settings(provider, quota_ready=quota_ready, usage_count=usage_count, daily_limit=daily_limit)
        st.caption("O Razync prepara as ações; você sempre confirma antes de qualquer alteração.")
        return

    started_at = monotonic()
    with st.status("Analisando sua solicitação…", expanded=True) as status:
        st.write("Consultando somente os dados necessários da sua conta.")
        result = _answer_question(
            question,
            profile=profile,
            transactions=transactions,
            invoices=invoices,
            das_rows=das_rows,
            obligations=obligations,
            documents=documents,
            annual_limit=annual_limit,
            current_year=current_year,
            current_page="Assistente Razync",
            fallback_answer=fallback_answer,
        )
        status.update(label="Preparando resposta e próximas ações…", state="running")
        resources = _prepare_resources(
            question,
            profile=profile,
            transactions=transactions,
            invoices=invoices,
            das_rows=das_rows,
            obligations=obligations,
            documents=documents,
            current_year=current_year,
        )
        status.update(label="Resposta pronta", state="complete", expanded=False)

    elapsed = monotonic() - started_at
    trace = _trace_caption(result, current_year=current_year, elapsed=elapsed)
    _append_message(
        "assistant",
        result["answer"],
        metadata={
            "resources": bool(resources),
            "provider": result.get("provider"),
            "model": result.get("model"),
            "elapsed_seconds": round(elapsed, 3),
            "mode": mode,
        },
    )
    st.session_state["razync_ai_last_trace"] = trace
    st.session_state["razync_ai_last_resources"] = resources or {}
    st.session_state["razync_ai_last_resource_question"] = question
    st.session_state["razync_ai_flash_notices"] = result["notices"]
    st.rerun()
