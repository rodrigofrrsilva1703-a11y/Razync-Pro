from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from activity_center import build_activity_items
from fiscal_timeline import build_fiscal_timeline


def test_activity_center_prioritizes_overdue_and_upcoming_items():
    today = date(2026, 9, 1)
    items = build_activity_items(
        profile={"cnpj": "", "main_activity": ""},
        transactions=pd.DataFrame(columns=["tx_date", "tx_type", "description", "value"]),
        das_rows=[
            {"competence": "2026-07", "due_date": today - timedelta(days=5), "status": "Pendente"},
            {"competence": "2026-09", "due_date": today + timedelta(days=10), "status": "Pendente"},
        ],
        obligations=[{"title": "Entrega teste", "due_date": today + timedelta(days=8), "status": "Pendente"}],
        documents=[],
        today=today,
    )
    assert any(item["page"] == "Meu MEI" for item in items["agora"])
    assert any(item["page"] == "DAS" and "Vencido" in item["detail"] for item in items["agora"])
    assert any(item["page"] == "Obrigações" for item in items["proximos"])


def test_fiscal_timeline_orders_overdue_before_future():
    today = date(2026, 9, 1)
    items = build_fiscal_timeline(
        das_rows=[
            {"competence": "2026-08", "due_date": today - timedelta(days=3), "status": "Pendente"},
            {"competence": "2026-09", "due_date": today + timedelta(days=12), "status": "Pendente"},
        ],
        obligations=[],
        today=today,
    )
    assert items[0]["status"] == "Atrasado"
    assert items[0]["page"] == "DAS"


def test_dashboard_and_fiscal_integrate_new_operational_views():
    dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
    fiscal = Path("fiscal_workspace.py").read_text(encoding="utf-8")
    assert 'st.expander("Central de Atividades"' in dashboard
    assert "build_activity_items(" in dashboard
    assert 'st.expander("Linha do tempo fiscal"' in fiscal
    assert "build_fiscal_timeline(" in fiscal
