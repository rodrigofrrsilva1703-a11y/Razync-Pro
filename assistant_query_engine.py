from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from io import StringIO

import pandas as pd


MONTHS_PT = {
    "janeiro": 1, "jan": 1,
    "fevereiro": 2, "fev": 2,
    "marco": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "maio": 5, "mai": 5,
    "junho": 6, "jun": 6,
    "julho": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "setembro": 9, "set": 9,
    "outubro": 10, "out": 10,
    "novembro": 11, "nov": 11,
    "dezembro": 12, "dez": 12,
}
NUMBER_WORDS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4,
    "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10,
    "onze": 11, "doze": 12,
}


@dataclass(frozen=True)
class Period:
    start: date
    end: date
    label: str


@dataclass(frozen=True)
class BusinessQueryResult:
    handled: bool
    kind: str
    summary: str
    period: Period | None = None
    table: pd.DataFrame | None = None
    confidence: str = "high"

    def csv_bytes(self) -> bytes | None:
        if self.table is None or self.table.empty:
            return None
        buffer = StringIO()
        self.table.to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8-sig")


def _plain(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in normalized if not unicodedata.combining(char)).lower()
    return re.sub(r"\s+", " ", text).strip()


def _last_day(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def _month_period(year: int, month: int) -> Period:
    start = date(year, month, 1)
    end = _last_day(year, month)
    return Period(start, end, f"{month:02d}/{year}")


def _parse_count(text: str, unit: str, default: int) -> int:
    match = re.search(rf"ultim[oa]s?\s+(\d+)\s+{unit}", text)
    if match:
        return max(1, min(60, int(match.group(1))))
    for word, number in NUMBER_WORDS.items():
        if re.search(rf"ultim[oa]s?\s+{word}\s+{unit}", text):
            return number
    return default


def parse_period(question: str, *, today: date | None = None, default_year: int | None = None) -> Period:
    today = today or date.today()
    default_year = default_year or today.year
    text = _plain(question)

    if "hoje" in text:
        return Period(today, today, "hoje")
    if "ontem" in text:
        yesterday = today - timedelta(days=1)
        return Period(yesterday, yesterday, "ontem")

    if any(term in text for term in ("mes passado", "ultimo mes", "mes anterior")):
        previous_end = date(today.year, today.month, 1) - timedelta(days=1)
        return _month_period(previous_end.year, previous_end.month)
    if any(term in text for term in ("este mes", "mes atual", "nesse mes", "neste mes")):
        return Period(date(today.year, today.month, 1), today, f"{today.month:02d}/{today.year} até hoje")

    if any(term in text for term in ("ano passado", "ultimo ano")):
        year = today.year - 1
        return Period(date(year, 1, 1), date(year, 12, 31), str(year))
    if any(term in text for term in ("este ano", "ano atual", "neste ano", "nesse ano")):
        return Period(date(today.year, 1, 1), today, f"{today.year} até hoje")

    if any(term in text for term in ("primeiro trimestre", "1 trimestre", "1o trimestre")):
        return Period(date(default_year, 1, 1), date(default_year, 3, 31), f"1º trimestre/{default_year}")
    if any(term in text for term in ("segundo trimestre", "2 trimestre", "2o trimestre")):
        return Period(date(default_year, 4, 1), date(default_year, 6, 30), f"2º trimestre/{default_year}")
    if any(term in text for term in ("terceiro trimestre", "3 trimestre", "3o trimestre")):
        return Period(date(default_year, 7, 1), date(default_year, 9, 30), f"3º trimestre/{default_year}")
    if any(term in text for term in ("quarto trimestre", "4 trimestre", "4o trimestre")):
        return Period(date(default_year, 10, 1), date(default_year, 12, 31), f"4º trimestre/{default_year}")

    day_count = _parse_count(text, r"dias?", 30)
    if re.search(r"ultim[oa]s?.{0,12}dias?", text):
        return Period(today - timedelta(days=day_count - 1), today, f"últimos {day_count} dias")

    month_count = _parse_count(text, r"mes(?:es)?", 3)
    if re.search(r"ultim[oa]s?.{0,16}mes(?:es)?", text):
        month_index = today.year * 12 + today.month - month_count
        start_year, zero_month = divmod(month_index, 12)
        start = date(start_year, zero_month + 1, 1)
        return Period(start, today, f"últimos {month_count} meses")

    range_match = re.search(
        r"(?:entre|de)\s+([a-z]+)(?:\s+de\s+(20\d{2}))?\s+(?:e|a|ate)\s+([a-z]+)(?:\s+de\s+(20\d{2}))?",
        text,
    )
    if range_match:
        first_name, first_year, second_name, second_year = range_match.groups()
        if first_name in MONTHS_PT and second_name in MONTHS_PT:
            y1 = int(first_year or second_year or default_year)
            y2 = int(second_year or first_year or default_year)
            m1, m2 = MONTHS_PT[first_name], MONTHS_PT[second_name]
            start = date(y1, m1, 1)
            end = _last_day(y2, m2)
            if end >= start:
                return Period(start, end, f"{m1:02d}/{y1} a {m2:02d}/{y2}")

    numeric_month = re.search(r"\b(0?[1-9]|1[0-2])/(20\d{2})\b", text)
    if numeric_month:
        return _month_period(int(numeric_month.group(2)), int(numeric_month.group(1)))

    named_months = [(name, month) for name, month in MONTHS_PT.items() if re.search(rf"\b{name}\b", text)]
    if named_months:
        name, month = named_months[0]
        year_match = re.search(rf"\b{name}\s+(?:de\s+)?(20\d{{2}})\b", text)
        return _month_period(int(year_match.group(1)) if year_match else default_year, month)

    year_match = re.search(r"\b(20\d{2})\b", text)
    if year_match:
        year = int(year_match.group(1))
        return Period(date(year, 1, 1), date(year, 12, 31), str(year))

    return Period(date(default_year, 1, 1), today if default_year == today.year else date(default_year, 12, 31), f"{default_year} até hoje" if default_year == today.year else str(default_year))


def parse_comparison_periods(question: str, *, today: date | None = None, default_year: int | None = None) -> tuple[Period, Period] | None:
    today = today or date.today()
    default_year = default_year or today.year
    text = _plain(question)
    month_names = [(name, month) for name, month in MONTHS_PT.items() if re.search(rf"\b{name}\b", text)]
    unique: list[tuple[str, int]] = []
    seen = set()
    for name, month in month_names:
        if month not in seen:
            unique.append((name, month)); seen.add(month)
    if len(unique) >= 2 and any(term in text for term in ("compare", "comparar", "comparacao", "versus", " vs ", "com ")):
        years = [int(y) for y in re.findall(r"\b20\d{2}\b", text)]
        y1 = years[0] if years else default_year
        y2 = years[1] if len(years) > 1 else y1
        return _month_period(y1, unique[0][1]), _month_period(y2, unique[1][1])
    if any(term in text for term in ("compare com o mes passado", "comparado ao mes passado", "versus mes passado")):
        current = Period(date(today.year, today.month, 1), today, f"{today.month:02d}/{today.year} até hoje")
        previous_end = date(today.year, today.month, 1) - timedelta(days=1)
        previous = _month_period(previous_end.year, previous_end.month)
        return previous, current
    return None


def _money(value: float) -> str:
    return f"R$ {float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _filter_period(transactions: pd.DataFrame, period: Period) -> pd.DataFrame:
    if transactions.empty:
        return transactions.copy()
    frame = transactions.copy()
    frame["tx_date"] = pd.to_datetime(frame["tx_date"], errors="coerce")
    dates = frame["tx_date"].dt.date
    return frame[(dates >= period.start) & (dates <= period.end)].copy()


def _period_totals(frame: pd.DataFrame) -> tuple[float, float, float]:
    if frame.empty:
        return 0.0, 0.0, 0.0
    revenue = float(frame.loc[frame["tx_type"] == "Receita", "value"].sum())
    expense = float(frame.loc[frame["tx_type"] == "Despesa", "value"].sum())
    return revenue, expense, revenue - expense


def _period_comparison(transactions: pd.DataFrame, first: Period, second: Period) -> BusinessQueryResult:
    first_rows = _filter_period(transactions, first)
    second_rows = _filter_period(transactions, second)
    r1, e1, result1 = _period_totals(first_rows)
    r2, e2, result2 = _period_totals(second_rows)
    table = pd.DataFrame([
        {"Período": first.label, "Receitas": r1, "Despesas": e1, "Resultado": result1},
        {"Período": second.label, "Receitas": r2, "Despesas": e2, "Resultado": result2},
    ])
    delta = result2 - result1
    direction = "melhorou" if delta > 0 else "piorou" if delta < 0 else "ficou estável"
    summary = (
        f"Comparando {first.label} com {second.label}, o resultado {direction}: "
        f"foi de {_money(result1)} para {_money(result2)} ({_money(delta)} de diferença). "
        f"Receitas: {_money(r1)} → {_money(r2)}; despesas: {_money(e1)} → {_money(e2)}."
    )
    return BusinessQueryResult(True, "comparison", summary, second, table)


def _monthly_performance(frame: pd.DataFrame, *, best: bool = True) -> BusinessQueryResult:
    if frame.empty:
        return BusinessQueryResult(True, "monthly_performance", "Não há movimentações no período solicitado.")
    working = frame.copy()
    working["Mês"] = working["tx_date"].dt.to_period("M").astype(str)
    grouped = working.pivot_table(index="Mês", columns="tx_type", values="value", aggfunc="sum", fill_value=0).reset_index()
    if "Receita" not in grouped: grouped["Receita"] = 0.0
    if "Despesa" not in grouped: grouped["Despesa"] = 0.0
    grouped["Resultado"] = grouped["Receita"] - grouped["Despesa"]
    grouped = grouped.rename(columns={"Receita": "Receitas", "Despesa": "Despesas"})
    chosen = grouped.loc[grouped["Resultado"].idxmax() if best else grouped["Resultado"].idxmin()]
    adjective = "melhor" if best else "pior"
    summary = f"O {adjective} mês do período foi {chosen['Mês']}, com resultado de {_money(chosen['Resultado'])}, receitas de {_money(chosen['Receitas'])} e despesas de {_money(chosen['Despesas'])}."
    return BusinessQueryResult(True, "monthly_performance", summary, table=grouped.sort_values("Mês"))


def _top_counterparties(frame: pd.DataFrame, tx_type: str, label: str) -> BusinessQueryResult:
    rows = frame[frame["tx_type"] == tx_type].copy() if not frame.empty else frame
    if rows.empty or "counterparty" not in rows.columns:
        return BusinessQueryResult(True, "counterparty", f"Não há {label.lower()} identificados nas movimentações desse período.")
    names = rows["counterparty"].fillna("").astype(str).str.strip()
    rows = rows[names.ne("")].copy()
    if rows.empty:
        return BusinessQueryResult(True, "counterparty", f"As movimentações existem, mas os {label.lower()} não estão preenchidos nos lançamentos desse período.")
    grouped = rows.groupby("counterparty")["value"].agg(["sum", "count"]).sort_values("sum", ascending=False).reset_index()
    grouped.columns = [label[:-1] if label.endswith("s") else label, "Valor", "Movimentações"]
    top = grouped.iloc[0]
    summary = f"O principal {label[:-1].lower() if label.endswith('s') else label.lower()} no período foi **{top.iloc[0]}**, com {_money(top['Valor'])} em {int(top['Movimentações'])} movimentação(ões)."
    return BusinessQueryResult(True, "counterparty", summary, table=grouped.head(20))


def _category_analysis(frame: pd.DataFrame, tx_type: str) -> BusinessQueryResult:
    rows = frame[frame["tx_type"] == tx_type].copy() if not frame.empty else frame
    noun = "despesas" if tx_type == "Despesa" else "receitas"
    if rows.empty:
        return BusinessQueryResult(True, "category", f"Não há {noun} no período solicitado.")
    grouped = rows.assign(category=rows["category"].fillna("Outros").astype(str)).groupby("category")["value"].sum().sort_values(ascending=False).reset_index()
    grouped.columns = ["Categoria", "Valor"]
    total = float(grouped["Valor"].sum())
    top = grouped.iloc[0]
    share = float(top["Valor"]) / total * 100 if total else 0
    summary = f"A categoria que mais pesa nas {noun} é **{top['Categoria']}**, com {_money(top['Valor'])} ({share:.1f}% do total de {_money(total)})."
    return BusinessQueryResult(True, "category", summary, table=grouped)


def _why_cash_changed(transactions: pd.DataFrame, *, today: date, default_year: int) -> BusinessQueryResult:
    current = Period(date(today.year, today.month, 1), today, f"{today.month:02d}/{today.year} até hoje")
    previous_end = date(today.year, today.month, 1) - timedelta(days=1)
    previous = _month_period(previous_end.year, previous_end.month)
    current_rows = _filter_period(transactions, current)
    previous_rows = _filter_period(transactions, previous)
    cr, ce, cres = _period_totals(current_rows)
    pr, pe, pres = _period_totals(previous_rows)
    delta = cres - pres
    expense_delta = ce - pe
    revenue_delta = cr - pr
    causes = []
    if expense_delta > 0:
        causes.append(f"despesas aumentaram {_money(expense_delta)}")
    if revenue_delta < 0:
        causes.append(f"receitas caíram {_money(abs(revenue_delta))}")
    if not causes:
        causes.append("a variação vem da combinação entre receitas e despesas do período")
    summary = f"O resultado do mês atual está {_money(abs(delta))} {'abaixo' if delta < 0 else 'acima'} do mês anterior. A principal leitura pelos números é que {' e '.join(causes)}."
    category = _category_analysis(current_rows, "Despesa")
    table = category.table
    return BusinessQueryResult(True, "cash_change", summary + (f" {category.summary}" if category.summary else ""), current, table)


def analyze_business_question(
    question: str,
    transactions: pd.DataFrame,
    *,
    today: date | None = None,
    default_year: int | None = None,
) -> BusinessQueryResult:
    today = today or date.today()
    default_year = default_year or today.year
    text = _plain(question)
    if transactions.empty:
        if any(term in text for term in ("receita", "despesa", "gasto", "lucro", "resultado", "caixa", "moviment")):
            return BusinessQueryResult(True, "empty", "Ainda não há movimentações cadastradas para responder essa consulta.")
        return BusinessQueryResult(False, "unknown", "")

    comparisons = parse_comparison_periods(question, today=today, default_year=default_year)
    if comparisons:
        return _period_comparison(transactions, comparisons[0], comparisons[1])

    period = parse_period(question, today=today, default_year=default_year)
    frame = _filter_period(transactions, period)

    if any(term in text for term in ("por que meu caixa caiu", "porque meu caixa caiu", "por que o caixa caiu", "caixa caiu", "resultado caiu", "resultado piorou")):
        return _why_cash_changed(transactions, today=today, default_year=default_year)

    if any(term in text for term in ("qual mes deu mais lucro", "melhor mes", "mes mais lucrativo", "maior resultado")):
        return _monthly_performance(frame, best=True)
    if any(term in text for term in ("pior mes", "mes deu prejuizo", "menor resultado")):
        return _monthly_performance(frame, best=False)

    if any(term in text for term in ("cliente mais", "qual cliente", "quem mais me pagou", "mais me pagou", "maior cliente")):
        return _top_counterparties(frame, "Receita", "Clientes")
    if any(term in text for term in ("fornecedor mais", "qual fornecedor", "quem eu mais paguei", "maior fornecedor")):
        return _top_counterparties(frame, "Despesa", "Fornecedores")

    if any(term in text for term in ("categoria", "mais pesa", "maiores gastos", "maior gasto", "onde mais gasto", "onde gastei mais")):
        return _category_analysis(frame, "Despesa")

    revenue, expense, result = _period_totals(frame)
    if any(term in text for term in ("quanto gastei", "quanto paguei", "total de despesas", "minhas despesas", "gastos")):
        return BusinessQueryResult(True, "expense_total", f"No período {period.label}, suas despesas somam **{_money(expense)}** em {int((frame['tx_type'] == 'Despesa').sum())} movimentação(ões).", period)
    if any(term in text for term in ("quanto faturei", "quanto recebi", "total de receitas", "minhas receitas", "faturamento")):
        return BusinessQueryResult(True, "revenue_total", f"No período {period.label}, suas receitas somam **{_money(revenue)}** em {int((frame['tx_type'] == 'Receita').sum())} movimentação(ões).", period)
    if any(term in text for term in ("lucro", "resultado", "saldo", "como ficou meu caixa", "como esta meu caixa")):
        margin = (result / revenue * 100) if revenue else 0.0
        return BusinessQueryResult(True, "result", f"No período {period.label}, o resultado é **{_money(result)}**: {_money(revenue)} de receitas menos {_money(expense)} de despesas. A margem sobre as receitas é {margin:.1f}%.", period)

    if any(term in text for term in ("movimentacoes", "movimentacao", "lancamentos", "lancamento")) and any(term in text for term in ("quantas", "quantos", "lista", "mostrar", "mostre", "traga")):
        visible = frame[[column for column in ["tx_date", "tx_type", "description", "category", "value", "counterparty", "payment_method"] if column in frame.columns]].copy()
        if "tx_date" in visible:
            visible["tx_date"] = visible["tx_date"].dt.date
        return BusinessQueryResult(True, "transactions", f"Encontrei {len(visible)} movimentação(ões) no período {period.label}, totalizando {_money(revenue)} de receitas e {_money(expense)} de despesas.", period, visible.tail(200))

    return BusinessQueryResult(False, "unknown", "", period)
