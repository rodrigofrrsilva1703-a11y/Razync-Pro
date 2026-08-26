from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ConversationStyle:
    key: str
    label: str
    directive: str


_STYLES = {
    "supportive": ConversationStyle(
        key="supportive",
        label="Acolhedor e resolutivo",
        directive=(
            "Use um tom humano, calmo e acolhedor, sem soar artificial. Reconheça a preocupação ou dificuldade em uma "
            "frase curta quando isso ajudar e avance rapidamente para a solução. Não dramatize, não infantilize e não use "
            "frases vazias de motivação."
        ),
    ),
    "decisive": ConversationStyle(
        key="decisive",
        label="Direto para decisão",
        directive=(
            "Seja objetivo e seguro. Comece pela recomendação ou conclusão, explique o motivo com os dados relevantes e "
            "mostre o próximo passo mais útil. Evite introduções longas e excesso de opções."
        ),
    ),
    "teaching": ConversationStyle(
        key="teaching",
        label="Didático e simples",
        directive=(
            "Explique em linguagem cotidiana, sem jargão desnecessário. Quando um termo contábil, fiscal ou financeiro for "
            "importante, explique em uma frase e conecte ao que o usuário vê no Razync."
        ),
    ),
    "analytical": ConversationStyle(
        key="analytical",
        label="Analítico e consultivo",
        directive=(
            "Seja preciso e consultivo. Compare números quando houver base, destaque o que realmente mudou e priorize o "
            "impacto para o negócio. Não despeje métricas sem explicar por que elas importam."
        ),
    ),
    "continuation": ConversationStyle(
        key="continuation",
        label="Continuidade natural",
        directive=(
            "Trate a mensagem como continuação da conversa. Recupere o assunto recente antes de responder, não repita "
            "explicações já dadas e não peça novamente informações que já estejam no histórico. Se a referência continuar "
            "ambígua e houver risco de agir sobre o item errado, faça somente a pergunta mínima necessária."
        ),
    ),
    "neutral": ConversationStyle(
        key="neutral",
        label="Natural e profissional",
        directive=(
            "Converse de forma natural, profissional e próxima. Use frases claras, varie a construção das respostas e evite "
            "parecer um formulário, manual ou robô."
        ),
    ),
}


def _plain(value: str) -> str:
    text = str(value or "").lower().strip()
    return re.sub(r"\s+", " ", text)


def _recent_text(conversation: Iterable[dict] | None, limit: int = 4) -> str:
    parts: list[str] = []
    for item in list(conversation or [])[-limit:]:
        role = str(item.get("role") or "")
        if role not in {"user", "assistant"}:
            continue
        content = _plain(str(item.get("content") or ""))
        if content:
            parts.append(content[:500])
    return " ".join(parts)


def select_conversation_style(question: str, conversation: Iterable[dict] | None = None) -> ConversationStyle:
    text = _plain(question)
    recent = _recent_text(conversation)

    continuation_terms = (
        "e agora", "e depois", "e antes", "e o outro", "e o anterior", "e aquele", "e esse", "e isso",
        "qual deles", "qual delas", "por que isso", "e no mes passado", "e no mês passado", "continua", "pode continuar",
    )
    supportive_terms = (
        "não sei", "nao sei", "não entendi", "nao entendi", "me ajuda", "estou perdido", "to perdido",
        "estou preocupado", "preocupado", "deu errado", "erro", "problema", "socorro",
    )
    teaching_terms = (
        "o que é", "o que e", "como funciona", "me explica", "explique", "não entendo", "nao entendo",
        "qual a diferença", "qual a diferenca", "por que",
    )
    decisive_terms = (
        "o que eu faço", "o que faço", "o que devo", "qual devo", "qual é melhor", "qual e melhor",
        "por onde começo", "primeiro", "prioridade", "decidir", "decisão", "decisao",
    )
    analytical_terms = (
        "analise", "análise", "compare", "comparar", "resultado", "margem", "cresceu", "caiu",
        "projeção", "projecao", "tendência", "tendencia", "porcentagem", "percentual",
    )

    if any(term in text for term in continuation_terms) or (len(text.split()) <= 4 and recent and text in {"e agora?", "e agora", "e depois?", "e depois", "qual deles?", "qual deles"}):
        return _STYLES["continuation"]
    if any(term in text for term in supportive_terms):
        return _STYLES["supportive"]
    if any(term in text for term in teaching_terms):
        return _STYLES["teaching"]
    if any(term in text for term in decisive_terms):
        return _STYLES["decisive"]
    if any(term in text for term in analytical_terms):
        return _STYLES["analytical"]

    if recent:
        if any(term in recent for term in supportive_terms):
            return _STYLES["supportive"]
        if any(term in recent for term in analytical_terms):
            return _STYLES["analytical"]
    return _STYLES["neutral"]


def build_conversation_directive(question: str, conversation: Iterable[dict] | None = None) -> tuple[str, str]:
    style = select_conversation_style(question, conversation)
    return style.label, style.directive
