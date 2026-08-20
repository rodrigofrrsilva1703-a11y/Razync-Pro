from __future__ import annotations

import unittest
from datetime import date

import pandas as pd

from smart_insights import build_proactive_insights


class SmartInsightsTests(unittest.TestCase):
    def test_detects_expense_growth(self):
        transactions = pd.DataFrame([
            {"tx_date": "2026-07-10", "tx_type": "Despesa", "value": 100.0, "category": "Materiais", "document_number": "1"},
            {"tx_date": "2026-08-10", "tx_type": "Despesa", "value": 160.0, "category": "Materiais", "document_number": "2"},
            {"tx_date": "2026-08-11", "tx_type": "Receita", "value": 500.0, "category": "Serviços", "document_number": "3"},
        ])
        insights = build_proactive_insights(
            profile={}, transactions=transactions, invoices=pd.DataFrame(),
            das_rows=[], obligations=[], documents=[], annual_limit=81000.0,
            current_year=2026, today=date(2026, 8, 20),
        )
        self.assertTrue(any(item["title"] == "Despesas aceleraram neste mês" for item in insights))

    def test_prioritizes_overdue_das(self):
        transactions = pd.DataFrame([
            {"tx_date": "2026-08-10", "tx_type": "Receita", "value": 1000.0, "category": "Serviços", "document_number": "10"},
        ])
        insights = build_proactive_insights(
            profile={}, transactions=transactions, invoices=pd.DataFrame(),
            das_rows=[{"status": "Pendente", "due_date": "2026-08-10"}],
            obligations=[], documents=[], annual_limit=81000.0,
            current_year=2026, today=date(2026, 8, 20),
        )
        self.assertEqual(insights[0]["title"], "DAS em atraso precisa de atenção")
        self.assertEqual(insights[0]["page"], "DAS")

    def test_empty_snapshot_returns_no_insight(self):
        transactions = pd.DataFrame(columns=["tx_date", "tx_type", "value", "category", "document_number"])
        insights = build_proactive_insights(
            profile={}, transactions=transactions, invoices=pd.DataFrame(),
            das_rows=[], obligations=[], documents=[], annual_limit=81000.0,
            current_year=2026, today=date(2026, 8, 20),
        )
        self.assertEqual(insights, [])


if __name__ == "__main__":
    unittest.main()
