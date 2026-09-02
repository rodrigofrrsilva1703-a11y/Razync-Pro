from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from compact_cards import navigation_card
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


def build_activity_items(
    *,
    profile: dict,
    transactions: pd.DataFrame,
    das_rows: list[dict],
    obligations: list[dict],
    documents: list[dict],
    today: date | None = None,
) -> dict[str, list[dict]]:
    current = today or date.today()
    horizon = current + timedelta(days=30)
    now: list[dict] = []
    upcoming: list[dict] = []
    recent: list[dict] = []

    if not profile.get("cnpj") or not profile.get("main_activity"):
        now.append({"title": "Completar dados do MEI", "detail": "Cadastro essencial incompleto", "page": "Meu MEI", "level": "warn"})

    for row in das_rows:
        due = _coerce_date(row.get("due_date"))
        status = das_status(row.get("status", "Pendente"), due, current)
        competence = str(row.get("competence") or "competência")
        if status == "Atrasado":
            now.append({"title": f"DAS {competence}", "detail": "Vencido e precisa de revisão", "page": "DAS", "level": "danger"})
        elif status == "Pendente" and due and current <= due <= horizon:
            upcoming.append({"title": f"DAS {competence}", "detail": f"Vence em {due.strftime('%d/%m')}", "page": "DAS", "level": "warn"})

    for row in obligations:
        due = _coerce_date(row.get("due_date"))
        status = str(row.get("status") or "Pendente")
        title = str(row.get("title") or "Obrigação")
        if status != "Concluído" and due and due < current:
            now.append({"title": title, "detail": "Obrigação vencida", "page": "Obrigações", "level": "danger"})
        elif status != "Concluído" and due and current <= due <= horizon:
            upcoming.append({"title": title, "detail": f"Vence em {due.strftime('%d/%m')}", "page": "Obrigações", "level": "warn"})

    if not documents:
        now.append({"title": "Organizar documentos", "detail": "Nenhum arquivo armazenado", "page": "Documentos", "level": "info"})

    if not transactions.empty:
        ordered = transactions.sort_values("tx_date", ascending=False).head(4)
        for row in ordered.itertuples():
            tx_date = _coerce_date(getattr(row, "tx_date", None))
            tx_type = str(getattr(row, "tx_type", "Movimentação"))
            description = str(getattr(row, "description", "") or "Sem descrição")
            recent.append({
                "title": description[:48],
                "detail": f"{tx_type} · {tx_date.strftime('%d/%m') if tx_date else 'data não informada'}",
                "page": "Movimentações",
                "level": "ok",
            })

    return {
        "agora": now[:6],
        "proximos": sorted(upcoming, key=lambda item: item["detail"])[:6],
        "recentes": recent[:4],
    }


def render_activity_center(*, items: dict[str, list[dict]], navigate) -> None:
    """Render a compact operational center without duplicating business state."""
    tabs = st.tabs(["Agora", "Próximos 30 dias", "Atividade recente"])
    groups = (items.get("agora", []), items.get("proximos", []), items.get("recentes", []))
    empty_texts = (
        "Nenhuma pendência crítica identificada agora.",
        "Nenhum vencimento cadastrado para os próximos 30 dias.",
        "Ainda não há movimentações recentes para exibir.",
    )
    for tab, group, empty_text in zip(tabs, groups, empty_texts):
        with tab:
            if not group:
                st.caption(empty_text)
                continue
            columns = st.columns(2)
            for index, item in enumerate(group):
                with columns[index % 2]:
                    if navigation_card(
                        item["title"],
                        key=f"activity_{index}_{item['page']}_{item['title']}",
                        help_text=item["detail"],
                    ):
                        navigate(item["page"])
