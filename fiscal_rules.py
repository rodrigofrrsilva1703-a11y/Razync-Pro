from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from typing import Iterable

MEI_ANNUAL_LIMIT = 81_000.0
MEI_MONTHLY_PROPORTION = 6_750.0
DASN_DEADLINE_MONTH = 5
DASN_DEADLINE_DAY = 31


def annual_limit_for(opening_date: date | None, year: int, configured_limit: float | None = None) -> float:
    configured = float(configured_limit or 0)
    base = configured if configured > 0 else MEI_ANNUAL_LIMIT
    if opening_date and opening_date.year == year:
        return MEI_MONTHLY_PROPORTION * (13 - opening_date.month)
    return base


def das_due_date(competence: str) -> date:
    year, month = map(int, competence.split("-"))
    if month == 12:
        due_year, due_month = year + 1, 1
    else:
        due_year, due_month = year, month + 1
    day = min(20, monthrange(due_year, due_month)[1])
    due = date(due_year, due_month, day)
    while due.weekday() >= 5:
        due += timedelta(days=1)
    return due


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
    if today <= deadline and today.month >= 1:
        alerts.append(("info", "DASN-SIMEI", f"Confira a declaração anual antes de {deadline.strftime('%d/%m/%Y')}."))

    if not alerts:
        alerts.append(("ok", "Tudo em ordem", "Nenhum alerta crítico foi identificado com os dados registrados."))
    return alerts
