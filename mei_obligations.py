from __future__ import annotations

from datetime import date

from fiscal_rules import competence_list, das_due_date, dasn_deadline, monthly_report_due_date


def _status(due: date, today: date) -> str:
    if due < today:
        return "Vencida"
    if (due - today).days <= 7:
        return "Próxima"
    return "Futura"


def automatic_obligations(year: int, opening_date: date | None = None, today: date | None = None) -> list[dict]:
    today = today or date.today()
    rows: list[dict] = []

    start_month = 1
    if opening_date and opening_date.year == year:
        start_month = opening_date.month

    for comp in competence_list(year):
        month = int(comp[-2:])
        if month < start_month:
            continue

        das_due = das_due_date(comp)
        report_due = monthly_report_due_date(comp)
        rows.append({
            "Obrigação": f"DAS {comp}",
            "Competência": comp,
            "Categoria": "Fiscal",
            "Vencimento": das_due,
            "Status automático": _status(das_due, today),
            "Descrição": "Pagamento mensal do DAS-MEI.",
        })
        rows.append({
            "Obrigação": f"Relatório Mensal {comp}",
            "Competência": comp,
            "Categoria": "Contábil",
            "Vencimento": report_due,
            "Status automático": _status(report_due, today),
            "Descrição": "Preencher o Relatório Mensal de Receitas Brutas e arquivar com os documentos do mês.",
        })

    deadline = dasn_deadline(year + 1)
    rows.append({
        "Obrigação": f"DASN-SIMEI {year}",
        "Competência": str(year),
        "Categoria": "Declaração anual",
        "Vencimento": deadline,
        "Status automático": _status(deadline, today),
        "Descrição": "Transmitir a declaração anual referente ao ano-calendário anterior.",
    })
    for row in rows:
        row.update({
            "title": row["Obrigação"],
            "competence": row["Competência"],
            "category": row["Categoria"],
            "due_date": row["Vencimento"],
            "status": row["Status automático"],
            "details": row["Descrição"],
        })
    return sorted(rows, key=lambda x: x["Vencimento"])
