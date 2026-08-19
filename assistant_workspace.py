from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st

from ai_assistant import DEFAULT_MODEL, RazyncAIError, ask_razync_ai, build_safe_business_context


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
    model = _secret("OPENAI_MODEL") or DEFAULT_MODEL
    ai_enabled = bool(api_key.strip())

    status_left, status_right = st.columns([3, 1])
    with status_left:
        if ai_enabled:
            st.success("IA Razync ativa")
            st.caption("A IA recebe somente um resumo agregado dos seus dados. CNPJ, CPF, arquivos e credenciais não são enviados.")
        else:
            st.info("Modo inteligente local")
            st.caption("Adicione OPENAI_API_KEY aos Secrets para ativar a IA generativa. As respostas locais continuam disponíveis.")
    with status_right:
        if ai_enabled:
            st.caption(f"Modelo: {model}")

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
        if ai_enabled:
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
            except RazyncAIError:
                answer = fallback_answer(question)
                st.warning("A IA externa não respondeu agora. Usei a análise local do Razync para não interromper seu atendimento.")
        else:
            answer = fallback_answer(question)
        st.markdown(answer)

    st.session_state["razync_ai_messages"].append({"role": "assistant", "content": answer})
    if len(st.session_state["razync_ai_messages"]) > 20:
        st.session_state["razync_ai_messages"] = st.session_state["razync_ai_messages"][-20:]

    st.caption("As respostas usam os registros do Razync e podem conter interpretações. Para obrigações oficiais, confirme no portal competente ou com seu contador.")
