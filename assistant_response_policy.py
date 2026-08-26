from __future__ import annotations

import re
from typing import Iterable

from assistant_personality import select_conversation_style


_NUMERIC_TOKEN = re.compile(r"(?:R\$\s*)?\d[\d.]*?(?:,\d+)?%?")
_ROBOTIC_OPENINGS = (
    "olá! ", "olá, ", "claro! ", "com certeza! ", "certamente! ", "ótima pergunta! ", "excelente pergunta! ",
)


def _numeric_tokens(text: str) -> tuple[str, ...]:
    return tuple(_NUMERIC_TOKEN.findall(str(text or "")))


def normalize_response(answer: str) -> str:
    """Normalize presentation without changing facts, values or markdown structure."""
    text = str(answer or "").strip()
    if not text:
        return ""
    original_numbers = _numeric_tokens(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if _numeric_tokens(text) != original_numbers:
        return str(answer or "").strip()
    return text


def humanize_local_response(
    answer: str,
    *,
    question: str,
    source: str = "local",
    conversation: Iterable[dict] | None = None,
) -> str:
    """Give deterministic local answers the same conversational discipline as external AI.

    The factual answer is never rewritten. We only remove canned openings and, in a
    small set of safe situations, add a non-factual framing sentence. Numeric tokens
    are verified before returning the result.
    """
    text = normalize_response(answer)
    if not text:
        return text
    original_numbers = _numeric_tokens(text)
    lower = text.lower()
    for opening in _ROBOTIC_OPENINGS:
        if lower.startswith(opening):
            text = text[len(opening):].lstrip()
            break

    style = select_conversation_style(question, conversation)
    source_key = str(source or "").lower()
    prefix = ""
    if style.key == "supportive" and not text.lower().startswith(("entendi", "não encontrei", "ainda não", "nenhum")):
        prefix = "Entendi. "
    elif style.key == "continuation" and source_key not in {"action", "ação"}:
        prefix = "Seguindo o que estávamos vendo: "

    candidate = prefix + text
    if _numeric_tokens(candidate) != original_numbers:
        return normalize_response(answer)
    return candidate


def response_policy_directive() -> str:
    return (
        "Mantenha consistência com as respostas locais do Razync: seja natural e objetivo, preserve exatamente os números "
        "e fatos do contexto, não repita saudações, não use elogios automáticos e não prometa que uma ação foi executada. "
        "Em continuidade de conversa, conecte a resposta ao assunto recente e evite pedir novamente dados já informados."
    )
