from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date
from typing import Iterable

import pandas as pd
from openai import OpenAI


DEFAULT_MODEL = "gpt-5.6-luna"


class RazyncAIError(RuntimeError):
    """Raised when the external AI provider cannot answer safely."""


def _date_value(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _money(value: float) -> float:
    return round(float(value or 0.0), 2)


def _percent_change(current: float, previous: float) -> float | None:
    previous = float(previous or 0.0)
    current = float(current or 0.0)
    if previous == 0:
        return None if current == 0 else 100.0
    return round(((current - previous) / abs(previous)) * 100.0, 2)


def _redact_conversation_text(value: str) -> str:
    """Remove common direct identifiers before a chat turn is sent externally."""
    text = str(value or "")[:1200]
    patterns = (
        (r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email removido]"),
        (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "[CPF removido]"),
        (r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b", "[CNPJ removido]"),
        (r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4}[-\s]?\d{4}(?!\d)", "[telefone removido]"),
        (r"\b(?:sk|AIza)[A-Za-z0-9_\-]{12,}\b", "[credencial removida]"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text.strip()


def build_safe_conversation_history(
    messages: Iterable[dict] | None,
    *,
    current_question: str | None = None,
    limit: int = 6,
) -> list[dict]:
    """Build a short, sanitized memory of the current assistant conversation."""
    safe: list[dict] = []
    for item in list(messages or [])[-max(limit + 2, limit):]:
        role = str(item.get("role") or "")
        if role not in {"user", "assistant"}:
            continue
        content = _redact_conversation_text(str(item.get("content") or ""))
        if not content:
            continue
        if current_question and role == "user" and content == _redact_conversation_text(current_question):
            continue
        safe.append({"role": role, "content": content})
    return safe[-limit:]


def build_safe_business_context(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: Iterable[dict],
    obligations: Iterable[dict],
    documents: Iterable[dict],
    annual_limit: float,
    year: int,
    today: date | None = None,
) -> dict:
    """Build an aggregate-only context without direct personal identifiers."""
    today = today or date.today()
    tx = transactions.copy()
    if tx.empty:
        year_tx = tx
    else:
        dates = pd.to_datetime(tx["tx_date"], errors="coerce")
        tx = tx.assign(tx_date=dates)
        year_tx = tx[tx["tx_date"].dt.year == year]

    revenue_rows = year_tx[year_tx["tx_type"] == "Receita"] if not year_tx.empty else year_tx
    expense_rows = year_tx[year_tx["tx_type"] == "Despesa"] if not year_tx.empty else year_tx
    revenue = _money(revenue_rows["value"].sum()) if not revenue_rows.empty else 0.0
    expense = _money(expense_rows["value"].sum()) if not expense_rows.empty else 0.0

    monthly: list[dict] = []
    for month in range(1, 13):
        if year_tx.empty:
            month_rows = year_tx
        else:
            month_rows = year_tx[year_tx["tx_date"].dt.month == month]
        month_revenue = _money(month_rows[month_rows["tx_type"] == "Receita"]["value"].sum()) if not month_rows.empty else 0.0
        month_expense = _money(month_rows[month_rows["tx_type"] == "Despesa"]["value"].sum()) if not month_rows.empty else 0.0
        monthly.append(
            {
                "month": month,
                "revenue": month_revenue,
                "expense": month_expense,
                "result": _money(month_revenue - month_expense),
            }
        )

    def category_totals(frame: pd.DataFrame) -> list[dict]:
        if frame.empty or "category" not in frame.columns:
            return []
        grouped = frame.assign(category=frame["category"].fillna("Outros").astype(str))
        totals = grouped.groupby("category")["value"].sum().sort_values(ascending=False).head(8)
        return [{"category": str(name), "value": _money(value)} for name, value in totals.items()]

    revenue_categories = category_totals(revenue_rows)
    expense_categories = category_totals(expense_rows)

    largest_expense = None
    if not expense_rows.empty:
        row = expense_rows.loc[expense_rows["value"].astype(float).idxmax()]
        largest_expense = {
            "date": row["tx_date"].date().isoformat() if hasattr(row["tx_date"], "date") else str(row["tx_date"]),
            "category": str(row.get("category") or "Outros"),
            "value": _money(row.get("value") or 0),
        }

    current_month = monthly[today.month - 1] if 1 <= today.month <= 12 else {"revenue": 0.0, "expense": 0.0, "result": 0.0}
    previous_month = monthly[today.month - 2] if today.month > 1 else {"revenue": 0.0, "expense": 0.0, "result": 0.0}
    elapsed_months = max(1, today.month if year == today.year else 12)
    average_monthly_revenue = _money(revenue / elapsed_months)
    average_monthly_expense = _money(expense / elapsed_months)
    projected_revenue = _money((revenue / elapsed_months) * 12) if elapsed_months else 0.0
    margin_percent = round(((revenue - expense) / revenue) * 100.0, 2) if revenue else None
    top_expense_share = None
    if expense and expense_categories:
        top_expense_share = round((float(expense_categories[0]["value"]) / expense) * 100.0, 2)

    invoice_rows = invoices.copy()
    if invoice_rows.empty:
        emitted_count = cancelled_count = 0
        invoice_total = 0.0
    else:
        statuses = invoice_rows.get("status", pd.Series(index=invoice_rows.index, dtype=str)).fillna("Emitida").astype(str)
        emitted = invoice_rows[statuses == "Emitida"]
        emitted_count = int(len(emitted))
        cancelled_count = int((statuses == "Cancelada").sum())
        invoice_total = _money(emitted["amount"].sum()) if "amount" in emitted else 0.0

    tx_docs = set()
    if not year_tx.empty and "document_number" in year_tx.columns:
        tx_docs = set(year_tx["document_number"].fillna("").astype(str).str.strip())
        tx_docs.discard("")
    unreconciled_invoices = 0
    if not invoice_rows.empty and "number" in invoice_rows.columns:
        active = invoice_rows[invoice_rows.get("status", "Emitida") == "Emitida"] if "status" in invoice_rows.columns else invoice_rows
        numbers = active["number"].fillna("").astype(str).str.strip()
        unreconciled_invoices = int((~numbers.isin(tx_docs)).sum())

    das_counter = Counter()
    next_das_due = None
    for item in das_rows:
        status = str(item.get("status") or "Pendente")
        due = _date_value(item.get("due_date"))
        if status == "Pago":
            das_counter["paid"] += 1
        elif due and due < today:
            das_counter["overdue"] += 1
        else:
            das_counter["pending"] += 1
            if due and (next_das_due is None or due < next_das_due):
                next_das_due = due

    obligation_counter = Counter()
    next_obligation_due = None
    for item in obligations:
        if str(item.get("status") or "") == "Concluído":
            obligation_counter["done"] += 1
            continue
        due = _date_value(item.get("due_date"))
        if due and due < today:
            obligation_counter["overdue"] += 1
        else:
            obligation_counter["pending"] += 1
            if due and (next_obligation_due is None or due < next_obligation_due):
                next_obligation_due = due

    document_categories = Counter(str(item.get("category") or "Outros") for item in documents)
    missing_document_numbers = 0
    if not year_tx.empty and "document_number" in year_tx.columns:
        missing_document_numbers = int(year_tx["document_number"].fillna("").astype(str).str.strip().eq("").sum())

    opening = _date_value(profile.get("opening_date"))
    remaining = max(float(annual_limit or 0) - revenue, 0.0)
    limit_usage = (revenue / float(annual_limit) * 100.0) if annual_limit else 0.0
    projected_limit_usage = (projected_revenue / float(annual_limit) * 100.0) if annual_limit else 0.0

    return {
        "reference_date": today.isoformat(),
        "reference_year": year,
        "business": {
            "activity_type": str(profile.get("activity_type") or "Não informado"),
            "opening_year": opening.year if opening else None,
            "has_employee": bool(profile.get("has_employee", False)),
        },
        "financial": {
            "revenue": revenue,
            "expense": expense,
            "result": _money(revenue - expense),
            "margin_percent": margin_percent,
            "annual_limit": _money(annual_limit),
            "remaining_limit": _money(remaining),
            "limit_usage_percent": round(limit_usage, 2),
            "projected_revenue": projected_revenue,
            "projected_limit_usage_percent": round(projected_limit_usage, 2),
            "average_monthly_revenue": average_monthly_revenue,
            "average_monthly_expense": average_monthly_expense,
            "current_month": current_month,
            "previous_month": previous_month,
            "month_over_month": {
                "revenue_change_percent": _percent_change(current_month["revenue"], previous_month["revenue"]),
                "expense_change_percent": _percent_change(current_month["expense"], previous_month["expense"]),
                "result_change_percent": _percent_change(current_month["result"], previous_month["result"]),
            },
            "revenue_by_category": revenue_categories,
            "expense_by_category": expense_categories,
            "top_expense_category_share_percent": top_expense_share,
            "largest_expense": largest_expense,
            "monthly": monthly,
            "transactions_count": int(len(year_tx)),
            "transactions_without_document_number": missing_document_numbers,
        },
        "fiscal": {
            "invoices_emitted": emitted_count,
            "invoices_cancelled": cancelled_count,
            "invoice_total": invoice_total,
            "invoices_unreconciled": unreconciled_invoices,
            "das_paid": das_counter["paid"],
            "das_pending": das_counter["pending"],
            "das_overdue": das_counter["overdue"],
            "next_das_due": next_das_due.isoformat() if next_das_due else None,
            "days_until_next_das": (next_das_due - today).days if next_das_due else None,
            "obligations_pending": obligation_counter["pending"],
            "obligations_overdue": obligation_counter["overdue"],
            "next_obligation_due": next_obligation_due.isoformat() if next_obligation_due else None,
            "days_until_next_obligation": (next_obligation_due - today).days if next_obligation_due else None,
        },
        "documents": {
            "count": int(sum(document_categories.values())),
            "by_category": dict(document_categories),
        },
        "privacy": {
            "direct_identifiers_included": False,
            "raw_documents_included": False,
            "transaction_descriptions_included": False,
            "counterparties_included": False,
        },
    }


INSTRUCTIONS = """
Você é o Assistente Razync, um copiloto financeiro e fiscal para MEI no Brasil.
Responda em português do Brasil, de forma clara, prática e específica ao negócio analisado.

REGRAS DE ANÁLISE
- Antes de responder, identifique mentalmente a intenção da pergunta e selecione somente os dados relevantes do contexto.
- Use SOMENTE o contexto agregado do Razync para afirmar valores, quantidades, datas e situações do usuário.
- Quando houver comparação disponível, compare mês atual x anterior, média mensal, margem, projeção e concentração de despesas antes de concluir.
- Diferencie sempre: dado registrado, cálculo/projeção do Razync e recomendação.
- Não transforme ausência de dados em conclusão. Diga o que falta quando necessário.
- Não invente lançamentos, documentos, clientes, pagamentos, regras fiscais, prazos ou fatos externos.

QUALIDADE DA RESPOSTA
- Comece pela conclusão mais útil, não por uma explicação genérica.
- Sustente a conclusão com 2 a 4 evidências numéricas quando existirem.
- Aponte causa provável somente quando o contexto permitir; caso contrário, trate como hipótese.
- Termine com 1 a 3 próximos passos concretos e priorizados quando fizer sentido.
- Em perguntas de continuidade, use a memória curta da conversa para entender referências como “isso”, “esse gasto” ou “e no mês passado?”.
- Evite repetir o mesmo resumo em respostas consecutivas.
- Prefira respostas entre 3 e 7 parágrafos curtos ou poucos tópicos, conforme a complexidade.

SEGURANÇA E LIMITES
- Você é consultivo: não diga que pagou, declarou, emitiu, alterou ou excluiu algo.
- Não peça senha, token, CPF, CNPJ, dados bancários completos ou credenciais gov.br.
- Para legislação, alíquotas, regras ou prazos que possam ter mudado e não estejam no contexto, oriente confirmação em fonte oficial ou com profissional responsável.
- Não revele raciocínio interno; entregue apenas a conclusão, evidências e recomendações úteis.
""".strip()


def build_ai_prompt(question: str, *, context: dict, conversation: Iterable[dict] | None = None) -> str:
    safe_history = build_safe_conversation_history(conversation, current_question=question)
    history_payload = json.dumps(safe_history, ensure_ascii=False, separators=(",", ":")) if safe_history else "[]"
    return (
        "Pergunta atual do usuário:\n"
        + question.strip()
        + "\n\nMemória curta e sanitizada desta conversa (JSON):\n"
        + history_payload
        + "\n\nContexto agregado e autorizado do Razync (JSON):\n"
        + json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    )


def ask_razync_ai(
    question: str,
    *,
    context: dict,
    api_key: str,
    model: str = DEFAULT_MODEL,
    conversation: Iterable[dict] | None = None,
) -> str:
    if not question or not question.strip():
        raise ValueError("A pergunta não pode ficar vazia.")
    if not api_key or not api_key.strip():
        raise RazyncAIError("OPENAI_API_KEY não configurada.")

    payload = build_ai_prompt(question, context=context, conversation=conversation)
    try:
        client = OpenAI(api_key=api_key.strip(), timeout=25.0, max_retries=1)
        response = client.responses.create(
            model=(model or DEFAULT_MODEL).strip(),
            instructions=INSTRUCTIONS,
            input=payload,
            store=False,
            max_output_tokens=1100,
        )
        answer = (response.output_text or "").strip()
    except Exception as exc:
        raise RazyncAIError("A IA está temporariamente indisponível.") from exc
    if not answer:
        raise RazyncAIError("A IA não retornou uma resposta utilizável.")
    return answer
