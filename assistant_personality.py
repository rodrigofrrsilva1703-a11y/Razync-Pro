from __future__ import annotations

import re
from dataclasses import dataclass


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
            "frase curta quando isso ajudar, e avance rapidamente para a solução. Não dramatize, não infantilize e não use "
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


def select_conversation_style(question: str) -> ConversationStyle:
    text = _plain(question)

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

    if any(term in text for term in supportive_terms):
        return _STYLES["supportive"]
    if any(term in text for term in teaching_terms):
        return _STYLES["teaching"]
    if any(term in text for term in decisive_terms):
        return _STYLES["decisive"]
    if any(term in text for term in analytical_terms):
        return _STYLES["analytical"]
    return _STYLES["neutral"]


def build_conversation_directive(question: str) -> tuple[str, str]:
    style = select_conversation_style(question)
    return style.label, style.directive
