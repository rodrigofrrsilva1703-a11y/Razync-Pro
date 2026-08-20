from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


def _as_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if value is None:
        return None
    try:
        return pd.to_datetime(value, errors="coerce").date()
    except Exception:
        return None


def _pct_change(current: float, previous: float) -> float | None:
    if previous <= 0:
        return None
    return ((current - previous) / previous) * 100.0


def build_proactive_insights(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    annual_limit: float,
    current_year: int,
    today: date | None = None,
) -> list[dict]:
    """Return prioritized, local-only insights from data already loaded in session.

    This function never calls an external provider or the database. It is deliberately
    deterministic so the Dashboard can render it without extra network round-trips.
    """
    today = today or date.today()
    insights: list[dict] = []

    tx = transactions.copy()
    if not tx.empty:
        tx["tx_date"] = pd.to_datetime(tx["tx_date"], errors="coerce")
        tx = tx[tx["tx_date"].dt.year == current_year]

    current_month = today.month
    previous_month = current_month - 1
    current_rows = tx[tx["tx_date"].dt.month == current_month] if not tx.empty else tx
    previous_rows = tx[tx["tx_date"].dt.month == previous_month] if not tx.empty and previous_month >= 1 else tx.iloc[0:0]

    def total(frame: pd.DataFrame, tx_type: str) -> float:
        if frame.empty:
            return 0.0
        return float(frame.loc[frame["tx_type"] == tx_type, "value"].sum())

    current_revenue = total(current_rows, "Receita")
    previous_revenue = total(previous_rows, "Receita")
    current_expense = total(current_rows, "Despesa")
    previous_expense = total(previous_rows, "Despesa")
    annual_revenue = total(tx, "Receita") if not tx.empty else 0.0

    revenue_change = _pct_change(current_revenue, previous_revenue)
    expense_change = _pct_change(current_expense, previous_expense)

    if expense_change is not None and expense_change >= 20:
        insights.append({
            "priority": 2,
            "level": "warn",
            "title": "Despesas aceleraram neste mês",
            "detail": f"As despesas estão {expense_change:.0f}% acima do mês anterior. Vale revisar as categorias que mais cresceram.",
            "page": "Análise Financeira",
            "question": "Minhas despesas aumentaram neste mês. Analise as categorias e me explique o que mais está pressionando meu resultado e o que devo revisar primeiro.",
        })

    if revenue_change is not None and revenue_change <= -20:
        insights.append({
            "priority": 2,
            "level": "warn",
            "title": "Receita caiu em relação ao mês anterior",
            "detail": f"As receitas estão {abs(revenue_change):.0f}% abaixo do mês anterior com os dados registrados até agora.",
            "page": "Análise Financeira",
            "question": "Minha receita caiu em relação ao mês anterior. Analise os dados disponíveis e me ajude a entender a situação e quais pontos devo acompanhar.",
        })
    elif revenue_change is not None and revenue_change >= 20:
        insights.append({
            "priority": 4,
            "level": "ok",
            "title": "Receita em crescimento",
            "detail": f"As receitas estão {revenue_change:.0f}% acima do mês anterior com os registros atuais.",
            "page": "Fluxo de Caixa",
            "question": "Minha receita cresceu neste mês. Analise se esse crescimento parece saudável considerando despesas, resultado e limite do MEI.",
        })

    if annual_limit > 0:
        used = annual_revenue / annual_limit
        months_elapsed = max(1, current_month)
        projected = annual_revenue / months_elapsed * 12
        if used >= 0.90 or projected >= annual_limit:
            insights.append({
                "priority": 1,
                "level": "danger",
                "title": "Risco de aproximação do limite do MEI",
                "detail": f"Você já utilizou {used * 100:.1f}% do limite monitorado. No ritmo médio atual, a projeção anual é R$ {projected:,.2f}.",
                "page": "Fiscal",
                "question": "Analise meu faturamento anual, o percentual do limite do MEI e a projeção. Explique o risco atual e o que devo acompanhar, sem afirmar regras que não estejam no contexto.",
            })
        elif used >= 0.70:
            insights.append({
                "priority": 2,
                "level": "warn",
                "title": "Faturamento merece acompanhamento",
                "detail": f"O Razync registra {used * 100:.1f}% do limite anual utilizado até agora.",
                "page": "Fiscal",
                "question": "Analise quanto do limite anual do MEI já foi utilizado e me diga como acompanhar o restante do ano com segurança.",
            })

    overdue_das = 0
    for row in das_rows:
        due = _as_date(row.get("due_date"))
        if str(row.get("status") or "Pendente") != "Pago" and due and due < today:
            overdue_das += 1
    if overdue_das:
        insights.append({
            "priority": 1,
            "level": "danger",
            "title": "DAS em atraso precisa de atenção",
            "detail": f"Há {overdue_das} competência(s) de DAS marcada(s) como não paga(s) após o vencimento.",
            "page": "DAS",
            "question": "Tenho DAS em atraso segundo os registros do Razync. Resuma minha situação e diga o que devo conferir no fluxo oficial do PGMEI.",
        })

    upcoming = []
    horizon = today + timedelta(days=7)
    for row in obligations:
        due = _as_date(row.get("due_date"))
        if str(row.get("status") or "") != "Concluído" and due and today <= due <= horizon:
            upcoming.append(due)
    if upcoming:
        next_due = min(upcoming)
        insights.append({
            "priority": 2,
            "level": "warn",
            "title": "Obrigação próxima do vencimento",
            "detail": f"Há {len(upcoming)} obrigação(ões) nos próximos 7 dias. A mais próxima vence em {next_due.strftime('%d/%m')}.",
            "page": "Obrigações",
            "question": "Tenho obrigações próximas do vencimento. Organize as prioridades usando somente as datas e situações registradas no Razync.",
        })

    if not tx.empty and "category" in tx.columns:
        expense_rows = tx[tx["tx_type"] == "Despesa"].copy()
        if not expense_rows.empty:
            grouped = expense_rows.assign(category=expense_rows["category"].fillna("Outros").astype(str)).groupby("category")["value"].sum().sort_values(ascending=False)
            if len(grouped):
                top_category = str(grouped.index[0])
                top_value = float(grouped.iloc[0])
                total_expense = float(grouped.sum())
                share = top_value / total_expense if total_expense else 0.0
                if share >= 0.35:
                    insights.append({
                        "priority": 3,
                        "level": "info",
                        "title": "Uma categoria concentra boa parte das despesas",
                        "detail": f"{top_category} representa cerca de {share * 100:.0f}% das despesas registradas no ano.",
                        "page": "Análise Financeira",
                        "question": f"A categoria {top_category} concentra uma parte relevante das minhas despesas. Analise esse peso no resultado e o que devo observar.",
                    })

    missing_docs = 0
    if not tx.empty and "document_number" in tx.columns:
        missing_docs = int(tx["document_number"].fillna("").astype(str).str.strip().eq("").sum())
    if missing_docs >= 5:
        insights.append({
            "priority": 4,
            "level": "info",
            "title": "Organização documental pode melhorar",
            "detail": f"Há {missing_docs} movimentações do ano sem número de documento vinculado.",
            "page": "Movimentações",
            "question": "Tenho várias movimentações sem número de documento. Explique por que organizar essa informação pode ajudar meu controle e fechamento mensal.",
        })

    if not transactions.empty and not insights:
        insights.append({
            "priority": 5,
            "level": "ok",
            "title": "Nenhum risco relevante detectado agora",
            "detail": "Com os dados atuais, o Razync não encontrou uma variação forte ou pendência prioritária entre os sinais monitorados.",
            "page": "Assistente Razync",
            "question": "Faça um check-up geral da minha situação financeira e fiscal com os dados agregados disponíveis e diga o que merece mais atenção agora.",
        })

    insights.sort(key=lambda item: (int(item["priority"]), item["title"]))
    return insights[:5]
