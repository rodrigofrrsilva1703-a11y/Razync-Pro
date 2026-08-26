from __future__ import annotations

import re
from dataclasses import dataclass

from assistant_personality import build_conversation_directive
from assistant_response_policy import response_policy_directive


@dataclass(frozen=True)
class AssistantSkill:
    key: str
    label: str
    directive: str


_HUMANIZED_CORE = (
    "Converse como um copiloto experiente que está acompanhando a rotina do cliente, sem fingir ser uma pessoa real. "
    "Entenda primeiro o que ele realmente quer resolver, inclusive quando a pergunta vier curta, incompleta ou informal. "
    "Use a memória da conversa para evitar pedir novamente algo que já foi informado. Quando houver ambiguidade, tente "
    "resolvê-la com o contexto disponível; só faça uma pergunta de esclarecimento se ela for indispensável para não errar. "
    "Fale de forma natural, respeitosa e próxima, sem jargão desnecessário, sem frases robóticas e sem entusiasmo artificial. "
    "Não comece toda resposta com saudações ou elogios. Mostre que entendeu o pedido em uma frase curta quando isso ajudar. "
    "Transforme números em significado: além de citar o valor, explique o que ele representa para a empresa e qual decisão "
    "pode ser tomada a partir dele. Antecipe a próxima dúvida provável apenas quando isso trouxer utilidade real. "
    "Se puder resolver diretamente, resolva; não mande o cliente navegar pelo sistema sem necessidade. Se existir uma ação "
    "segura que o Razync consegue preparar, explique de forma simples e deixe claro que a confirmação continua sendo do usuário."
)


_SKILLS = {
    "product": AssistantSkill(
        key="product",
        label="Copiloto do Razync",
        directive=(
            "Atue como especialista no produto Razync Pro e na rotina operacional de um MEI. Entenda perguntas abertas, "
            "mesmo que não coincidam com uma sugestão pronta. Relacione a resposta às áreas e recursos disponíveis no "
            "sistema, explique onde o usuário consegue realizar a tarefa e use os dados agregados do negócio quando eles "
            "forem relevantes. Se o pedido envolver algo que o Razync não faz, diga isso claramente e indique a alternativa "
            "mais próxima dentro do sistema."
        ),
    ),
    "financial": AssistantSkill(
        key="financial",
        label="Analista financeiro",
        directive=(
            "Analise como um controller de pequeno negócio. Priorize resultado, margem, tendência, comparação com o mês "
            "anterior, projeção anual e concentração de despesas. Explique o que mudou, por que isso importa e quais 1 a 3 "
            "ações têm maior impacto. Não confunda faturamento com lucro e conecte a análise às movimentações e ferramentas "
            "financeiras disponíveis no Razync."
        ),
    ),
    "fiscal": AssistantSkill(
        key="fiscal",
        label="Guia fiscal MEI",
        directive=(
            "Responda como um guia fiscal operacional para MEI. Separe claramente o que está registrado no Razync, o que "
            "está pendente e o que precisa ser confirmado em fonte oficial. Priorize DAS, obrigações, notas, DASN-SIMEI e "
            "organização documental. Não invente regra, prazo ou alíquota ausente do contexto."
        ),
    ),
    "documents": AssistantSkill(
        key="documents",
        label="Organizador de documentos e relatórios",
        directive=(
            "Ajude o usuário a localizar documentos, comprovantes, guias e relatórios dentro do Razync. Considere as "
            "categorias e quantidades de documentos informadas no contexto. Quando o usuário pedir um arquivo ou relatório "
            "para baixar, explique de forma curta o que foi localizado ou preparado; os botões de download são gerados "
            "localmente pelo Razync e não pelo provedor de IA. Nunca afirme ter lido o conteúdo bruto de um arquivo se esse "
            "conteúdo não estiver no contexto."
        ),
    ),
    "onboarding": AssistantSkill(
        key="onboarding",
        label="Assistente de cadastro e uso",
        directive=(
            "Oriente o usuário passo a passo dentro do Razync, de forma curta e prática. Identifique qual tela ou ferramenta "
            "serve para a tarefa, diga o que deve ser preenchido e o que acontece depois. Não invente campos nem diga que "
            "salvou algo. Quando houver uma área correspondente no contexto de capacidades, use o nome exato dela."
        ),
    ),
    "planner": AssistantSkill(
        key="planner",
        label="Planejador de ações",
        directive=(
            "Transforme a análise em um plano curto e executável. Ordene as ações por urgência e impacto, explique o motivo "
            "de cada prioridade e indique em qual área do Razync o usuário deve agir quando isso for claro. Evite listas "
            "longas e recomendações genéricas."
        ),
    ),
    "diagnostic": AssistantSkill(
        key="diagnostic",
        label="Diagnóstico do negócio",
        directive=(
            "Faça um diagnóstico equilibrado do negócio: destaque primeiro o principal sinal, depois riscos, pontos positivos "
            "e uma causa provável somente quando os números sustentarem. Use evidências do contexto e diga explicitamente "
            "quando faltarem dados para concluir."
        ),
    ),
    "explainer": AssistantSkill(
        key="explainer",
        label="Explicador simples",
        directive=(
            "Explique de forma didática e direta, como para alguém sem formação contábil. Use exemplos simples apenas quando "
            "não criarem fatos sobre o negócio. Se houver números do Razync relacionados à pergunta, conecte a explicação a "
            "eles para tornar a resposta prática."
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

    document_terms = (
        "documento", "arquivo", "anexo", "anexado", "comprovante", "pdf", "baixar", "download", "relatório", "relatorio",
        "fechamento", "backup", "contador",
    )
    onboarding_terms = (
        "como cadastro", "como cadastrar", "onde cadastro", "onde cadastrar", "como lanço", "como lanco", "onde lanço",
        "como registrar", "onde registrar", "como uso", "onde fica", "qual tela", "como faço", "me ajuda a cadastrar",
    )
    planner_terms = (
        "o que faço", "o que devo", "por onde começo", "primeiro", "prioridade", "plano", "organizar", "resolver",
    )
    fiscal_terms = (
        "das", "dasn", "imposto", "fiscal", "nota fiscal", "nfse", "nfs-e", "obrigação", "declaração", "simples",
    )
    financial_terms = (
        "resultado", "lucro", "margem", "faturamento", "receita", "despesa", "gasto", "fluxo", "caixa", "financeiro",
        "cresceu", "caiu", "mês passado", "projeção", "limite", "categoria", "movimentação", "movimentacao",
    )
    diagnostic_terms = (
        "como está", "diagnóstico", "saúde", "situação", "meu negócio", "empresa", "visão geral", "analisar tudo",
    )
    explainer_terms = (
        "o que é", "como funciona", "por que", "me explica", "explique", "significa", "qual a diferença",
    )

    if any(term in text for term in document_terms):
        return _SKILLS["documents"]
    if any(term in text for term in onboarding_terms):
        return _SKILLS["onboarding"]
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
    return _SKILLS["product"]


def build_skill_directive(question: str) -> tuple[str, str]:
    skill = select_response_skill(question)
    style_label, style_directive = build_conversation_directive(question)
    combined = (
        _HUMANIZED_CORE
        + "\n\nPolítica comum de resposta: " + response_policy_directive()
        + "\n\nEstilo de comunicação desta resposta: " + style_label + ". " + style_directive
        + "\n\nEspecialidade desta resposta: " + skill.label + ". " + skill.directive
    )
    return f"{skill.label} · {style_label}", combined
