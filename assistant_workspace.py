from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from ai_assistant import RazyncAIError, ask_razync_ai, build_safe_business_context
from ai_usage_store import AIUsageStoreError, get_ai_usage, release_ai_request, reserve_ai_request


DEFAULT_UI_MODEL = "gpt-5.4-mini"
DEFAULT_DAILY_REQUEST_LIMIT = 20

SUGGESTED_QUESTIONS = [
    "Quanto ainda posso faturar este ano?",
    "Como está meu resultado financeiro?",
    "Quais despesas mais pesam no meu negócio?",
    "Tenho DAS ou obrigações em atraso?",
    "Como estão minhas notas fiscais?",
    "O que devo organizar primeiro?",
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


def _diagnose_ai(api_key: str, model: str) -> tuple[bool, str]:
    """Run a tiny provider request and return a safe, user-facing diagnosis."""
    if not api_key.strip():
        return False, "OPENAI_API_KEY não foi encontrada nos Secrets do Streamlit."

    try:
        client = OpenAI(api_key=api_key.strip(), timeout=15.0, max_retries=0)
        response = client.responses.create(
            model=model.strip() or DEFAULT_UI_MODEL,
            input="Responda somente com OK.",
            store=False,
            max_output_tokens=8,
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
            return False, "A OpenAI rejeitou a configuração da chamada. Revise OPENAI_MODEL nos Secrets."
        return False, f"A OpenAI respondeu com erro HTTP {status or 'desconhecido'}. Revise a configuração da API."
    except Exception:
        return False, "Não foi possível validar a IA agora. A análise local do Razync continua disponível."


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
    api_key = _secret("OPENAI_API_KEY")
    model = _secret("OPENAI_MODEL") or DEFAULT_UI_MODEL
    ai_enabled = bool(api_key.strip())
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
        if ai_enabled and quota_ready:
            st.success("IA Razync configurada")
            st.caption("A IA recebe somente um resumo agregado dos seus dados. CNPJ, CPF, arquivos e credenciais não são enviados.")
        elif ai_enabled:
            st.warning("IA configurada, mas o controle de uso está indisponível")
            st.caption("Por segurança de custo, o Razync usará a análise local até o controle de quota voltar a responder.")
        else:
            st.info("Modo inteligente local")
            st.caption("OPENAI_API_KEY ainda não foi encontrada nos Secrets. As respostas locais continuam disponíveis.")
    with status_right:
        st.caption(f"Modelo: {model}")
        if ai_enabled and quota_ready:
            st.caption(f"Uso hoje (UTC): {usage_count}/{daily_limit}")

    with st.expander("Diagnóstico da IA", expanded=not ai_enabled):
        st.caption("Este teste faz uma chamada mínima à OpenAI e não envia dados do seu MEI. O teste não consome a quota diária do Assistente.")
        if st.button("Testar conexão da IA", key="razync_ai_diagnostic", width="stretch"):
            with st.spinner("Testando conexão..."):
                ok, diagnosis = _diagnose_ai(api_key, model)
            if ok:
                st.success(diagnosis)
            else:
                st.error(diagnosis)

    if "razync_ai_messages" not in st.session_state:
        st.session_state["razync_ai_messages"] = [
            {
                "role": "assistant",
                "content": "Olá! Sou o Assistente Razync. Posso analisar os dados que já estão no seu sistema e explicar sua situação financeira e fiscal em linguagem simples.",
            }
        ]

    for message in st.session_state["razync_ai_messages"][-10:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.caption("Sugestões")
    cols = st.columns(3)
    suggested = None
    for idx, question in enumerate(SUGGESTED_QUESTIONS):
        if cols[idx % 3].button(question, key=f"ai_suggestion_{idx}", width="stretch"):
            suggested = question

    question = st.chat_input("Pergunte ao Assistente Razync...")
    question = suggested or question
    if not question:
        st.caption("O assistente é consultivo e não executa pagamentos, declarações ou alterações sem sua confirmação nas ferramentas do Razync.")
        return

    st.session_state["razync_ai_messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        if ai_enabled and quota_ready and user_id is not None:
            try:
                allowed, reserved_count = reserve_ai_request(user_id, daily_limit)
            except AIUsageStoreError:
                allowed = False
                reserved_count = usage_count
                st.warning("O controle diário da IA não respondeu agora. Usei a análise local para evitar cobranças sem controle.")

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
                try:
                    with st.spinner("Analisando seus dados..."):
                        answer = ask_razync_ai(question, context=context, api_key=api_key, model=model)
                except RazyncAIError as exc:
                    try:
                        release_ai_request(user_id)
                    except AIUsageStoreError:
                        pass
                    answer = fallback_answer(question)
                    st.warning(f"A IA externa não respondeu ({exc}). Usei a análise local do Razync para não interromper seu atendimento.")
                except Exception:
                    try:
                        release_ai_request(user_id)
                    except AIUsageStoreError:
                        pass
                    answer = fallback_answer(question)
                    st.warning("A IA externa não respondeu agora. Usei a análise local do Razync.")
            else:
                answer = fallback_answer(question)
                if reserved_count >= daily_limit:
                    st.warning(f"A quota diária de {daily_limit} respostas de IA foi atingida. O limite reinicia às 00:00 UTC; usei a análise local do Razync.")
                else:
                    st.warning("Não foi possível reservar o uso da IA agora. Usei a análise local do Razync.")
        elif ai_enabled:
            answer = fallback_answer(question)
            st.warning("O controle de quota da IA está indisponível. Usei a análise local do Razync para evitar novas cobranças.")
        else:
            answer = fallback_answer(question)
        st.markdown(answer)

    st.session_state["razync_ai_messages"].append({"role": "assistant", "content": answer})
    if len(st.session_state["razync_ai_messages"]) > 20:
        st.session_state["razync_ai_messages"] = st.session_state["razync_ai_messages"][-20:]

    st.caption("As respostas usam os registros do Razync e podem conter interpretações. Para obrigações oficiais, confirme no portal competente ou com seu contador.")
