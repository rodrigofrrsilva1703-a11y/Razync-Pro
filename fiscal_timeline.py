from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from fiscal_rules import das_status


def _coerce_date(value):
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        return None if pd.isna(parsed) else parsed.date()
    except (TypeError, ValueError, OverflowError):
        return None


def build_fiscal_timeline(
    *,
    das_rows: list[dict],
    obligations: list[dict],
    today: date | None = None,
    days_ahead: int = 90,
) -> list[dict]:
    current = today or date.today()
    horizon = current + timedelta(days=days_ahead)
    items: list[dict] = []

    for row in das_rows:
        due = _coerce_date(row.get("due_date"))
        status = das_status(row.get("status", "Pendente"), due, current)
        if due and due > horizon and status != "Atrasado":
            continue
        items.append({
            "kind": "DAS",
            "title": f"DAS {row.get('competence') or ''}".strip(),
            "date": due,
            "status": status,
            "page": "DAS",
        })

    for row in obligations:
        due = _coerce_date(row.get("due_date"))
        if due and due > horizon and str(row.get("status") or "") != "Concluído":
            continue
        status = str(row.get("status") or "Pendente")
        if status == "Concluído":
            normalized = "Concluído"
        elif due and due < current:
            normalized = "Atrasado"
        elif due and due <= current + timedelta(days=30):
            normalized = "Próximo"
        else:
            normalized = "Pendente"
        items.append({
            "kind": "Obrigação",
            "title": str(row.get("title") or "Obrigação"),
            "date": due,
            "status": normalized,
            "page": "Obrigações",
        })

    rank = {"Atrasado": 0, "Próximo": 1, "Pendente": 2, "Concluído": 3, "Pago": 3}
    items.sort(key=lambda item: (rank.get(item["status"], 2), item["date"] or date.max))
    return items[:12]


def render_fiscal_timeline(*, items: list[dict], navigate) -> None:
    if not items:
        st.caption("Nenhum prazo fiscal cadastrado para exibir na linha do tempo.")
        return

    st.markdown(
        """
        <style>
        .rz-fiscal-timeline { display:grid; gap:.42rem; margin:.15rem 0 .65rem; }
        .rz-fiscal-line { display:grid; grid-template-columns:84px 1fr auto; align-items:center; gap:.7rem; padding:.55rem .7rem; border:1px solid var(--rz-border); border-radius:10px; background:var(--rz-surface); }
        .rz-fiscal-date { color:var(--rz-muted); font-size:.72rem; font-weight:700; }
        .rz-fiscal-title { color:var(--rz-text); font-size:.79rem; font-weight:720; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .rz-fiscal-status { border-radius:999px; padding:.25rem .48rem; font-size:.64rem; font-weight:800; background:var(--rz-soft); color:var(--rz-muted); }
        .rz-fiscal-status.atrasado { color:var(--rz-danger); background:color-mix(in srgb,var(--rz-danger) 11%,var(--rz-surface)); }
        .rz-fiscal-status.proximo { color:var(--rz-warning,#b9853d); background:color-mix(in srgb,#b9853d 10%,var(--rz-surface)); }
        .rz-fiscal-status.concluido, .rz-fiscal-status.pago { color:var(--rz-success); background:color-mix(in srgb,var(--rz-success) 11%,var(--rz-surface)); }
        @media(max-width:700px){ .rz-fiscal-line { grid-template-columns:70px 1fr; } .rz-fiscal-status { grid-column:2; width:max-content; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
    rows = []
    for item in items[:8]:
        due = item.get("date")
        date_label = due.strftime("%d/%m/%y") if due else "Sem data"
        status = str(item.get("status") or "Pendente")
        status_class = (
            status.lower()
            .replace("ó", "o")
            .replace("í", "i")
            .replace("ã", "a")
            .replace("ç", "c")
        )
        rows.append(
            f'<div class="rz-fiscal-line"><span class="rz-fiscal-date">{date_label}</span>'
            f'<span class="rz-fiscal-title">{item.get("title")}</span>'
            f'<span class="rz-fiscal-status {status_class}">{status}</span></div>'
        )
    st.markdown(f'<div class="rz-fiscal-timeline">{"".join(rows)}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Abrir DAS", key="timeline_open_das", width="stretch"):
        navigate("DAS")
    if c2.button("Abrir obrigações", key="timeline_open_obligations", width="stretch"):
        navigate("Obrigações")
