from pathlib import Path
import unittest

import pandas as pd

from ui_helpers import MONTH_NAMES_PT, filter_transactions, paginate_frame


def sample_transactions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"id": 1, "tx_type": "Receita", "category": "Serviços", "description": "Projeto Alfa", "counterparty": "Cliente Norte", "document_number": "NF-10"},
            {"id": 2, "tx_type": "Despesa", "category": "Marketing", "description": "Anúncio", "counterparty": "Agência Sul", "document_number": ""},
            {"id": 3, "tx_type": "Receita", "category": "Vendas", "description": "Pedido especial", "counterparty": "Loja Centro", "document_number": "PV-20"},
        ]
    )


def test_filters_use_the_complete_history_and_literal_search():
    frame = sample_transactions()

    assert filter_transactions(frame, tx_type="Receita")["id"].tolist() == [1, 3]
    assert filter_transactions(frame, category="Marketing")["id"].tolist() == [2]
    assert filter_transactions(frame, search="nf-10")["id"].tolist() == [1]
    assert filter_transactions(frame, search="cliente norte")["id"].tolist() == [1]
    assert filter_transactions(frame, search="[")["id"].tolist() == []


def test_pagination_clamps_invalid_pages_after_filtering():
    frame = pd.DataFrame({"id": range(1, 122)})

    first, total, current, pages = paginate_frame(frame, page=-3, page_size=50)
    assert (len(first), total, current, pages) == (50, 121, 1, 3)

    last, total, current, pages = paginate_frame(frame, page=99, page_size=50)
    assert (len(last), total, current, pages) == (21, 121, 3, 3)


def test_pagination_rejects_invalid_page_size():
    with unittest.TestCase().assertRaises(ValueError):
        paginate_frame(pd.DataFrame(), page=1, page_size=0)


def test_month_names_are_localized_and_chart_helper_is_defined():
    assert MONTH_NAMES_PT[0] == "Janeiro"
    assert MONTH_NAMES_PT[-1] == "Dezembro"

    app_source = Path("app.py").read_text(encoding="utf-8")
    assert "calendar.month_name" not in app_source
    assert "themed_plotly_chart(" not in app_source
    assert "apply_plot_theme(fig, UI_THEME)" in app_source
