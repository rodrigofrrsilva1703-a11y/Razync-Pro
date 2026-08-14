from __future__ import annotations

import pandas as pd


MONTH_NAMES_PT = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)


def filter_transactions(
    frame: pd.DataFrame,
    tx_type: str = "Todos",
    category: str = "Todas",
    search: str = "",
) -> pd.DataFrame:
    """Filter the complete transaction history before pagination."""
    view = frame.copy()
    if view.empty:
        return view

    if tx_type != "Todos":
        view = view[view["tx_type"] == tx_type]
    if category != "Todas":
        view = view[view["category"] == category]

    term = (search or "").strip().lower()
    if term:
        searchable = (
            view["description"].fillna("").astype(str) + " "
            + view["counterparty"].fillna("").astype(str) + " "
            + view["document_number"].fillna("").astype(str)
        ).str.lower()
        view = view[searchable.str.contains(term, regex=False)]

    return view


def paginate_frame(
    frame: pd.DataFrame,
    page: int,
    page_size: int = 50,
) -> tuple[pd.DataFrame, int, int, int]:
    """Return a safe page plus total rows, current page and page count."""
    if page_size <= 0:
        raise ValueError("page_size must be greater than zero")

    total = len(frame)
    max_page = max(1, (total + page_size - 1) // page_size)
    current_page = min(max(int(page), 1), max_page)
    offset = (current_page - 1) * page_size
    return frame.iloc[offset:offset + page_size].copy(), total, current_page, max_page
