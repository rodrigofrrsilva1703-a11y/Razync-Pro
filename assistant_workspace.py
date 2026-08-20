from __future__ import annotations

import re
from datetime import date
from typing import Callable

import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from ai_assistant import RazyncAIError, ask_razync_ai, build_safe_business_context
from ai_provider_router import ProviderChainError, run_provider_chain
from ai_usage_store import AIUsageStoreError, get_ai_usage, release_ai_request, reserve_ai_request
from assistant_resources import build_product_context, build_resource_bundle
from fiscal_rules import annual_limit_for
from gemini_provider import DEFAULT_GEMINI_MODEL, GeminiAIError, ask_razync_gemini, diagnose_gemini
from product_core import assistant_answer


DEFAULT_UI_MODEL = "gpt-5.4-mini"
DEFAULT_DAILY_REQUEST_LIMIT = 20
_SAFE_API_META = re.compile(r"^[A-Za-z0-9_.:\-/]{1,96}$")

SUGGESTED_QUESTIONS = [
    "Como está meu negócio hoje?",
    "O que mais está pesando nas despesas?",
    "O que preciso resolver primeiro?",
    "Onde cadastro uma nova receita?",
    "Quais documentos tenho salvos?",
    "Gere meu relatório financeiro em PDF",
]


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
        return int(user.get("id"))
    except (TypeError, ValueError):
        return None


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
    if "razync_ai_messages" not in st.session_state:
        st.session_state["razync_ai_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Sou o copiloto do Razync. Posso ajudar a usar o sistema, analisar seu financeiro e fiscal, "
                    "encontrar documentos, preparar relatórios e indicar a ferramenta certa para cada tarefa."
                ),
            }
        ]
    return st.session_state["razync_ai_messages"]


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

    if quota_ready:
        try:
            usage_count = get_ai_usage(user_id)
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
                    release_ai_request(user_id)
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
    except Exception:
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


def _store_turn(question: str, answer: str, resources: dict | None = None) -> None:
    messages = _ensure_messages()
    messages.append({"role": "user", "content": question})
    messages.append({"role": "assistant", "content": answer})
    if len(messages) > 24:
        st.session_state["razync_ai_messages"] = messages[-24:]
    st.session_state["razync_ai_last_resources"] = resources or {}
    st.session_state["razync_ai_last_resource_question"] = question


def render_floating_ai_assistant(*, user: dict, page: str, navigate) -> None:
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

    st.markdown("**Razync Copiloto**")
    st.caption("Converse sobre cadastro, financeiro, fiscal, documentos, relatórios ou qualquer ferramenta do sistema.")

    with st.container(key="floating_ai_messages"):
        for message in messages[-6:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with st.form("floating_ai_chat_form", clear_on_submit=True):
        question = st.text_input(
            "Mensagem",
            placeholder="Ex.: Gere meu relatório financeiro ou onde cadastro uma despesa?",
            label_visibility="collapsed",
        )
        sent = st.form_submit_button("Enviar", type="primary", width="stretch")

    if sent and question.strip():
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
        _render_notices(result["notices"])
        with st.chat_message("assistant"):
            st.markdown(result["answer"])

    _render_resources(
        st.session_state.get("razync_ai_last_resources"),
        key_prefix="floating_ai",
        current_page=page,
        navigate=navigate,
    )
    st.caption("A IA não executa pagamentos, exclusões ou transmissões fiscais sozinha.")


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
    provider = _provider_state()
    user_id = _current_user_id()
    daily_limit = _daily_request_limit()
    quota_ready = bool(user_id)
    usage_count = 0
    if quota_ready:
        try:
            usage_count = get_ai_usage(user_id)
        except AIUsageStoreError:
            quota_ready = False

    status_left, status_right = st.columns([3, 1])
    with status_left:
        if provider["ai_enabled"] and quota_ready:
            st.success(f"Copiloto Razync ativo — {provider['provider']}")
            if provider["fallback_enabled"]:
                st.caption("Fallback automático ativo: se o Gemini não responder, a OpenAI assume sem perder a conversa.")
            else:
                st.caption("Entende as ferramentas do sistema e recebe apenas contexto empresarial agregado. Arquivos brutos não são enviados ao provedor de IA.")
        elif provider["ai_enabled"]:
            st.warning("IA configurada, mas o controle de uso está indisponível")
            st.caption("Por segurança, o Razync usa a análise local até o controle voltar a responder.")
        else:
            st.info("Modo inteligente local")
            st.caption("Configure GEMINI_API_KEY ou OPENAI_API_KEY para ativar a IA externa. As ferramentas locais continuam funcionando.")
    with status_right:
        st.caption(f"Provedor: {provider['provider']}")
        st.caption(f"Modelo: {provider['model']}")
        if provider["ai_enabled"] and quota_ready:
            st.caption(f"Uso hoje (UTC): {usage_count}/{daily_limit}")
        if st.button("Nova conversa", key="razync_ai_new_chat", width="stretch"):
            st.session_state.pop("razync_ai_messages", None)
            st.session_state.pop("razync_ai_last_resources", None)
            st.session_state.pop("razync_ai_last_resource_question", None)
            st.rerun()

    with st.expander("Diagnóstico da IA", expanded=not provider["ai_enabled"]):
        if provider["gemini_enabled"]:
            st.caption("O teste não envia dados do MEI e não consome a quota interna do Assistente.")
        elif provider["openai_enabled"]:
            st.caption("O teste não envia dados do MEI e não consome a quota interna do Assistente.")
        else:
            st.caption("Configure GEMINI_API_KEY ou OPENAI_API_KEY nos Secrets para testar uma conexão externa.")
        if st.button("Testar conexão da IA", key="razync_ai_diagnostic", width="stretch"):
            with st.spinner("Testando conexão..."):
                if provider["gemini_enabled"]:
                    ok, diagnosis = diagnose_gemini(provider["gemini_api_key"], provider["gemini_model"])
                elif provider["openai_enabled"]:
                    ok, diagnosis = _diagnose_openai(provider["openai_api_key"], provider["openai_model"])
                else:
                    ok, diagnosis = False, "Nenhuma API externa foi configurada."
            if ok:
                st.success(diagnosis)
            else:
                st.error(diagnosis)

    messages = _ensure_messages()
    for message in messages[-12:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.caption("Você pode perguntar livremente. O copiloto entende tanto os números quanto as ferramentas do Razync.")
    cols = st.columns(3)
    suggested = None
    for idx, question_text in enumerate(SUGGESTED_QUESTIONS):
        if cols[idx % 3].button(question_text, key=f"ai_suggestion_{idx}", width="stretch"):
            suggested = question_text

    pending_question = st.session_state.pop("razync_ai_pending_question", None)
    typed_question = st.chat_input("Pergunte qualquer coisa sobre seu negócio ou sobre o Razync...")
    question = suggested or pending_question or typed_question
    if not question:
        _render_resources(
            st.session_state.get("razync_ai_last_resources"),
            key_prefix="full_ai_idle",
            current_page="Assistente Razync",
        )
        st.caption("O copiloto orienta e prepara recursos, mas ações sensíveis continuam exigindo confirmação nas ferramentas do Razync.")
        return

    question = question.strip()
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner(f"Analisando com {provider['provider']}..."):
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
        _render_notices(result["notices"])
        st.markdown(result["answer"])

    _store_turn(question, result["answer"], resources)
    _render_resources(resources, key_prefix="full_ai", current_page="Assistente Razync")
    st.caption("As respostas usam os registros do Razync. Para obrigações oficiais, confirme no portal competente ou com seu contador.")
