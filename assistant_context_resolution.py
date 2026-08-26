from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable

_MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
_MONTH_BY_NUMBER = {value: key for key, value in _MONTHS.items()}


@dataclass(frozen=True)
class ContextResolution:
    original_question: str
    resolved_question: str
    used_context: bool
    confidence: str
    reason: str


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in normalized if not unicodedata.combining(char)).lower()
    return re.sub(r"\s+", " ", text).strip()


def _recent_user_messages(conversation: Iterable[dict] | None, *, current_question: str, limit: int = 6) -> list[str]:
    current = _plain(current_question)
    messages: list[str] = []
    for item in list(conversation or [])[-max(limit * 2, limit):]:
        if str(item.get("role") or "") != "user":
            continue
        content = str(item.get("content") or "").strip()
        if not content or _plain(content) == current:
            continue
        messages.append(content)
    return messages[-limit:]


def _month_names(text: str) -> list[str]:
    plain = _plain(text)
    found: list[tuple[int, str]] = []
    for name in _MONTHS:
        match = re.search(rf"\b{name}\b", plain)
        if match:
            found.append((match.start(), name))
    return [name for _, name in sorted(found)]


def _year(text: str) -> str | None:
    match = re.search(r"\b(20\d{2})\b", str(text or ""))
    return match.group(1) if match else None


def _metric(text: str) -> str | None:
    plain = _plain(text)
    rules = (
        (("faturei", "faturamento", "faturou", "receita", "receitas"), "faturamento"),
        (("gastei", "gastos", "gasto", "despesa", "despesas"), "despesas"),
        (("resultado", "lucro", "sobrou", "saldo"), "resultado"),
        (("margem",), "margem"),
    )
    for terms, metric in rules:
        if any(term in plain for term in terms):
            return metric
    return None


def _metric_question(metric: str, month: str, year: str | None = None) -> str:
    suffix = f" de {year}" if year else ""
    if metric == "faturamento":
        return f"Quanto foi o faturamento em {month}{suffix}?"
    if metric == "despesas":
        return f"Quanto foram as despesas em {month}{suffix}?"
    if metric == "resultado":
        return f"Qual foi o resultado em {month}{suffix}?"
    if metric == "margem":
        return f"Qual foi a margem em {month}{suffix}?"
    return f"Analise {month}{suffix}."


def _recent_month_context(messages: list[str]) -> list[tuple[str, str | None, str | None]]:
    result: list[tuple[str, str | None, str | None]] = []
    for message in messages:
        months = _month_names(message)
        if not months:
            continue
        result.append((months[-1], _year(message), _metric(message)))
    return result


def resolve_contextual_question(
    question: str,
    conversation: Iterable[dict] | None,
    *,
    default_year: int | None = None,
) -> ContextResolution:
    """Resolve only high-confidence conversational references for deterministic local analysis.

    It never treats confirmation-like phrases as permission to execute actions. When the
    context is not clear enough, the original question is returned unchanged.
    """
    original = str(question or "").strip()
    plain = _plain(original)
    if not original:
        return ContextResolution(original, original, False, "low", "Pergunta vazia.")

    confirmation_like = {
        "faz isso", "faça isso", "faca isso", "pode fazer", "pode salvar", "confirma", "confirmar", "sim pode",
    }
    if plain in confirmation_like:
        return ContextResolution(original, original, False, "high", "Confirmações continuam no fluxo explícito de aprovação.")

    recent = _recent_user_messages(conversation, current_question=original)
    if not recent:
        return ContextResolution(original, original, False, "low", "Sem histórico recente suficiente.")

    latest = recent[-1]
    latest_metric = _metric(latest)
    latest_year = _year(latest) or (str(default_year) if default_year else None)
    current_months = _month_names(original)

    # Ex.: “Quanto faturei em julho?” -> “e agosto?”
    if len(current_months) == 1 and latest_metric:
        month = current_months[0]
        resolved = _metric_question(latest_metric, month, latest_year)
        return ContextResolution(original, resolved, True, "high", "Mês atual combinado com a métrica da pergunta anterior.")

    # Ex.: julho -> agosto -> “qual foi melhor?”
    if any(term in plain for term in ("qual foi melhor", "qual melhor", "qual deles", "qual delas", "qual foi maior")):
        month_context = _recent_month_context(recent)
        if len(month_context) >= 2:
            first, second = month_context[-2], month_context[-1]
            metric = second[2] or first[2]
            if metric and first[0] != second[0]:
                year1 = first[1] or latest_year
                year2 = second[1] or latest_year
                metric_label = {
                    "faturamento": "faturamento",
                    "despesas": "despesas",
                    "resultado": "resultado",
                    "margem": "margem",
                }.get(metric, metric)
                resolved = (
                    f"Compare {metric_label} de {first[0]} de {year1} com {second[0]} de {year2} e diga qual foi melhor."
                )
                return ContextResolution(original, resolved, True, "high", "Comparação inferida a partir dos dois últimos meses explicitamente discutidos.")

    # Ex.: “quanto faturei em agosto?” -> “e o mês anterior?”
    if any(term in plain for term in ("e o mes anterior", "e o mês anterior", "e antes", "e o anterior")):
        months = _month_names(latest)
        if latest_metric and months:
            month_number = _MONTHS[months[-1]]
            year = int(latest_year or default_year or 0)
            if month_number == 1 and year:
                previous_month, previous_year = 12, year - 1
            else:
                previous_month, previous_year = month_number - 1, year
            if previous_month >= 1:
                month_name = _MONTH_BY_NUMBER[previous_month]
                resolved = _metric_question(latest_metric, month_name, str(previous_year) if previous_year else None)
                return ContextResolution(original, resolved, True, "high", "Período anterior calculado a partir do último mês explícito.")

    return ContextResolution(original, original, False, "low", "Referência contextual insuficiente para reescrever com segurança.")
