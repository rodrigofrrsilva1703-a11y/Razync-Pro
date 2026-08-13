from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Iterable

# Regras oficiais monitoradas por ano. Mantemos as regras em um único módulo
# para facilitar atualização quando houver mudança normativa.
MEI_ANNUAL_LIMIT = 81_000.0
MEI_LIMITS_BY_YEAR = {
    2026: 81_000.0,
    2027: 110_000.0,
    2028: 140_000.0,
}
DASN_DEADLINE_MONTH = 5
DASN_DEADLINE_DAY = 31


def official_annual_limit(year: int) -> float:
    if year <= 2026:
        return 81_000.0
    if year == 2027:
        return 110_000.0
    return 140_000.0


def monthly_proportion_for(year: int) -> float:
    return official_annual_limit(year) / 12.0


def annual_limit_for(opening_date: date | None, year: int, configured_limit: float | None = None) -> float:
    official = official_annual_limit(year)
    configured = float(configured_limit or 0)

    # Bancos antigos podem ter 81 mil gravados como valor padrão. A partir de
    # 2027 esse valor legado não deve impedir a atualização automática oficial.
    if configured > 0 and not (year >= 2027 and abs(configured - 81_000.0) < 0.01):
        base = configured
    else:
        base = official

    if opening_date and opening_date.year == year:
        months = 13 - opening_date.month
        official_monthly = base / 12.0
        return official_monthly * months
    return base


def next_business_day_if_weekend(day: date) -> date:
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def das_due_date(competence: str) -> date:
    year, month = map(int, competence.split("-"))
    if month == 12:
        due_year, due_month = year + 1, 1
    else:
        due_year, due_month = year, month + 1
    due = date(due_year, due_month, min(20, monthrange(due_year, due_month)[1]))
    return next_business_day_if_weekend(due)


def monthly_report_due_date(competence: str) -> date:
    year, month = map(int, competence.split("-"))
    if month == 12:
        return date(year + 1, 1, 20)
    return date(year, month + 1, 20)


def competence_list(year: int) -> list[str]:
    return [f"{year}-{m:02d}" for m in range(1, 13)]


def das_status(current_status: str, due_date: date | None, today: date | None = None) -> str:
    today = today or date.today()
    if current_status == "Pago":
        return "Pago"
    if due_date and due_date < today:
        return "Atrasado"
    return "Pendente"


def dasn_deadline(delivery_year: int) -> date:
    return date(delivery_year, DASN_DEADLINE_MONTH, DASN_DEADLINE_DAY)


def build_alerts(
    revenue: float,
    annual_limit: float,
    das_rows: Iterable[dict],
    obligations: Iterable[dict],
    profile: dict,
    today: date | None = None,
) -> list[tuple[str, str, str]]:
    today = today or date.today()
    alerts: list[tuple[str, str, str]] = []
    pct = (revenue / annual_limit * 100) if annual_limit else 0
    if pct >= 100:
        alerts.append(("danger", "Limite de faturamento", "O faturamento registrado atingiu ou ultrapassou o limite monitorado."))
    elif pct >= 90:
        alerts.append(("danger", "Limite de faturamento", f"Você já utilizou {pct:.1f}% do limite anual monitorado."))
    elif pct >= 75:
        alerts.append(("warn", "Limite de faturamento", f"Você já utilizou {pct:.1f}% do limite anual monitorado."))

    overdue_das = 0
    due_soon_das = 0
    for item in das_rows:
        due = item.get("due_date")
        status = item.get("status", "Pendente")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due)
            except ValueError:
                due = None
        real_status = das_status(status, due, today)
        if real_status == "Atrasado":
            overdue_das += 1
        elif real_status == "Pendente" and due and 0 <= (due - today).days <= 7:
            due_soon_das += 1
    if overdue_das:
        alerts.append(("danger", "DAS em atraso", f"Há {overdue_das} competência(s) vencida(s) sem pagamento registrado."))
    elif due_soon_das:
        alerts.append(("warn", "DAS próximo do vencimento", f"Há {due_soon_das} competência(s) vencendo nos próximos 7 dias."))

    overdue_ob = 0
    for item in obligations:
        if item.get("status") == "Concluído":
            continue
        due = item.get("due_date")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due)
            except ValueError:
                due = None
        if due and due < today:
            overdue_ob += 1
    if overdue_ob:
        alerts.append(("danger", "Obrigações vencidas", f"Existem {overdue_ob} tarefa(s) vencida(s) na agenda."))

    if not profile.get("cnpj") or not profile.get("main_activity"):
        alerts.append(("warn", "Cadastro incompleto", "Complete CNPJ, atividade principal e data de abertura em Meu MEI."))

    deadline = dasn_deadline(today.year)
    if today <= deadline:
        alerts.append(("info", "DASN-SIMEI", f"Confira a declaração anual antes de {deadline.strftime('%d/%m/%Y')}."))

    if not alerts:
        alerts.append(("ok", "Tudo em ordem", "Nenhum alerta crítico foi identificado com os dados registrados."))
    return alerts
