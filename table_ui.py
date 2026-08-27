from __future__ import annotations

from collections.abc import Sized

import streamlit as st


def professional_table(
    data,
    *,
    column_config=None,
    column_order=None,
    key: str | None = None,
    max_visible_rows: int = 9,
    on_select="ignore",
    selection_mode="multi-row",
):
    """Render a consistent, compact business table with a bounded viewport."""
    try:
        row_count = len(data) if isinstance(data, Sized) else max_visible_rows
    except TypeError:
        row_count = max_visible_rows
    visible_rows = max(2, min(int(row_count), max_visible_rows))
    height = 38 + (visible_rows * 34)
    return st.dataframe(
        data,
        width="stretch",
        height=height,
        hide_index=True,
        row_height=34,
        column_config=column_config,
        column_order=column_order,
        key=key,
        on_select=on_select,
        selection_mode=selection_mode,
    )
