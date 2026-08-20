from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantSkill:
    key: str
    label: str
    directive: str


_SKILLS = {
    "financial": AssistantSkill(
        key="financial",
        label="Analista financeiro",
        directive=(
            "Analise como um controller de pequeno negócio. Priorize resultado, margem, tendência, "
            "comparação com o mês anterior, projeção anual e concentração de despesas. Explique o que mudou, "
            "por que isso importa e quais 1 a 3 ações têm maior impacto. Não confunda faturamento com lucro."
        ),
    ),
    "fiscal": AssistantSkill(
        key="fiscal",
        label="Guia fiscal MEI",
        directive=(
            "Responda como um guia fiscal operacional para MEI. Separe claramente o que está registrado no Razync, "
            "o que está pendente e o que precisa ser confirmado em fonte oficial. Priorize DAS, obrigações, notas, "
            "DASN-SIMEI e organização documental. Não invente regra, prazo ou alíquota ausente do contexto."
        ),
    ),
    "planner": AssistantSkill(
        key="planner",
        label="Planejador de ações",
        directive=(
            "Transforme a análise em um plano curto e executável. Ordene as ações por urgência e impacto, explique "
            "o motivo de cada prioridade e indique em qual área do Razync o usuário deve agir quando isso for óbvio. "
            "Evite listas longas e recomendações genéricas."
        ),
    ),
    "diagnostic": AssistantSkill(
        key="diagnostic",
        label="Diagnóstico do negócio",
        directive=(
            "Faça um diagnóstico equilibrado do negócio: destaque primeiro o principal sinal, depois riscos, pontos "
            "positivos e uma causa provável somente quando os números sustentarem. Use evidências do contexto e "
            "diga explicitamente quando faltarem dados para concluir."
        ),
    ),
    "explainer": AssistantSkill(
        key="explainer",
        label="Explicador simples",
        directive=(
            "Explique de forma didática e direta, como para alguém sem formação contábil. Use exemplos simples apenas "
            "quando não criarem fatos sobre o negócio. Se houver números do Razync relacionados à pergunta, conecte a "
            "explicação a eles para tornar a resposta prática."
        ),
    ),
}


def _normalize(question: str) -> str:
    text = str(question or "").lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def select_response_skill(question: str) -> AssistantSkill:
    """Choose one response skill locally; this never calls an external model."""
    text = _normalize(question)

    planner_terms = (
        "o que faço", "o que devo", "por onde começo", "primeiro", "prioridade", "plano", "organizar", "resolver",
    )
    fiscal_terms = (
        "das", "dasn", "imposto", "fiscal", "nota fiscal", "nfse", "nfs-e", "obrigação", "declaração", "simples",
    )
    financial_terms = (
        "resultado", "lucro", "margem", "faturamento", "receita", "despesa", "gasto", "fluxo", "caixa", "financeiro",
        "cresceu", "caiu", "mês passado", "projeção", "limite", "categoria",
    )
    diagnostic_terms = (
        "como está", "diagnóstico", "saúde", "situação", "meu negócio", "empresa", "visão geral", "analisar tudo",
    )
    explainer_terms = (
        "o que é", "como funciona", "por que", "me explica", "explique", "significa", "qual a diferença",
    )

    if any(term in text for term in planner_terms):
        return _SKILLS["planner"]
    if any(term in text for term in fiscal_terms):
        return _SKILLS["fiscal"]
    if any(term in text for term in financial_terms):
        return _SKILLS["financial"]
    if any(term in text for term in diagnostic_terms):
        return _SKILLS["diagnostic"]
    if any(term in text for term in explainer_terms):
        return _SKILLS["explainer"]
    return _SKILLS["diagnostic"]


def build_skill_directive(question: str) -> tuple[str, str]:
    skill = select_response_skill(question)
    return skill.label, skill.directive
