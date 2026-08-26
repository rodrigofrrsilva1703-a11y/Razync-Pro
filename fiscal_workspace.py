from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from business_tools import monthly_closing
from fiscal_rules import das_status
from ui_system import alert_card, section


def _display_date(value) -> str:
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return value or "—"
    return value.strftime("%d/%m/%Y") if hasattr(value, "strftime") else "—"


def _status_tone(status: str) -> str:
    normalized = status.casefold()
    if normalized in {"pago", "concluído", "concluido"}:
        return "ok"
    if normalized in {"atrasado", "vencido"}:
        return "danger"
    if normalized in {"pendente", "a vencer"}:
        return "warn"
    return "info"


def render_fiscal_workspace(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    invoices: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    current_year: int,
    annual_limit: float,
    annual_revenue: float,
    brl,
    navigate,
) -> None:
    """Integrated fiscal workspace for the core MEI routine."""
    today = date.today()
    overdue_das = [row for row in das_rows if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Atrasado"]
    pending_das = [row for row in das_rows if das_status(row.get("status", "Pendente"), row.get("due_date"), today) == "Pendente"]
    overdue_obligations = []
    for row in obligations:
        due = row.get("due_date")
        if isinstance(due, str):
            try:
                due = date.fromisoformat(due)
            except ValueError:
                due = None
        if row.get("status") != "Concluído" and due and due < today:
            overdue_obligations.append(row)

    section("Resumo fiscal", "Situação atual do DAS, notas e limite anual monitorado.")
    with st.container(key="fiscal_kpis"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("DAS em atraso", len(overdue_das))
        c2.metric("DAS pendentes", len(pending_das))
        c3.metric("Notas emitidas", len(invoices))
        c4.metric("Limite usado", f"{(annual_revenue / annual_limit * 100) if annual_limit else 0:.1f}%")

    if overdue_das:
        alert_card("danger", "DAS em atraso", f"Existem {len(overdue_das)} competência(s) vencida(s) para revisar.")
    elif overdue_obligations:
        alert_card("warn", "Obrigações vencidas", f"Existem {len(overdue_obligations)} tarefa(s) fiscal(is) vencida(s).")
    else:
        alert_card("ok", "Rotina fiscal sem alerta crítico", "Nenhum DAS atrasado ou obrigação manual vencida foi identificado.")

    section("Rotina fiscal", "Comece pela tarefa que corresponde ao que você precisa fazer agora.")
    a1, a2, a3, a4 = st.columns(4)
    if a1.button("DAS mensal", icon=":material/receipt_long:", width="stretch"):
        navigate("DAS")
    if a2.button("Notas fiscais", icon=":material/request_quote:", width="stretch"):
        navigate("Notas Fiscais")
    if a3.button("Prazos e obrigações", icon=":material/event:", width="stretch"):
        navigate("Obrigações")
    if a4.button("Declaração anual", icon=":material/description:", width="stretch"):
        navigate("DASN-SIMEI")

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        section("Competências do DAS", "Situação das guias já controladas no Razync.")
        if not das_rows:
            st.info("Nenhuma competência do DAS foi cadastrada ainda.")
        else:
            rows = []
            for row in das_rows:
                status = das_status(row.get("status", "Pendente"), row.get("due_date"), today)
                rows.append({
                    "Competência": row.get("competence"),
                    "Vencimento": row.get("due_date"),
                    "Valor": float(row.get("amount") or 0),
                    "Situação": status,
                })
            status_rows = []
            for row in rows[-6:]:
                status = str(row["Situação"])
                status_rows.append(
                    '<div class="rz-status-row" role="row">'
                    f'<strong>{escape(str(row["Competência"] or "Sem competência"))}</strong>'
                    f'<span>{escape(_display_date(row["Vencimento"]))}<br><small>{escape(brl(row["Valor"]))}</small></span>'
                    f'<span><b class="rz-pill rz-pill-{_status_tone(status)}">{escape(status)}</b></span></div>'
                )
            st.markdown(
                '<div class="rz-status-table" role="table" aria-label="Competências do DAS">'
                '<div class="rz-status-row rz-status-head" role="row"><span>Competência</span><span>Vencimento e valor</span><span>Situação</span></div>'
                f'{"".join(status_rows)}</div>',
                unsafe_allow_html=True,
            )
            with st.expander("Ver histórico completo do DAS"):
                st.dataframe(
                    pd.DataFrame(rows).tail(12),
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "Vencimento": st.column_config.DateColumn(format="DD/MM/YYYY"),
                        "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
                    },
                )

    with right:
        section("Fechamento atual", "Resumo do mês para saber se a documentação está organizada.")
        closing = monthly_closing(transactions, invoices, documents, das_rows, today.year, today.month)
        st.metric("Organização do mês", f"{closing['score']}%")
        st.progress(closing["score"] / 100)
        pending = [item for item in closing["checklist"] if not item["OK"]]
        if pending:
            for item in pending[:3]:
                st.caption(f"• {item['Item']}: {item['Detalhe']}")
            if st.button("Abrir fechamento mensal", width="stretch"):
                navigate("Fechamento Mensal")
        else:
            st.success("Fechamento do mês sem pendências no checklist.")

    section("Notas e documentos", "Acompanhe emissão e organização sem navegar por várias telas.")
    n1, n2, n3 = st.columns(3)
    n1.metric("Notas cadastradas", len(invoices))
    n2.metric("Documentos armazenados", len(documents))
    n3.metric("Faturamento no ano", brl(annual_revenue))

    q1, q2, q3 = st.columns(3)
    if q1.button("Importar NFS-e", width="stretch"):
        navigate("Importar NFS-e")
    if q2.button("Relatório mensal", width="stretch"):
        navigate("Relatório Mensal")
    if q3.button("Documentos", width="stretch"):
        navigate("Documentos")

    with st.expander("Mais recursos fiscais"):
        st.caption("Use estas ferramentas quando precisar de uma conferência mais detalhada.")
        b1, b2 = st.columns(2)
        if b1.button("Fechamento mensal completo", width="stretch"):
            navigate("Fechamento Mensal")
        if b2.button("Espaço do contador", width="stretch"):
            navigate("Espaço do Contador")

