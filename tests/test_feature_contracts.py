import unittest
from datetime import date

import pandas as pd

from business_tools import financial_analysis, monthly_closing
from mei_obligations import automatic_obligations


class FeatureContractTests(unittest.TestCase):
    def test_empty_financial_analysis_matches_the_ui_contract(self):
        analysis = financial_analysis(pd.DataFrame(), 2026)
        self.assertEqual(analysis["expense"], 0.0)
        self.assertIn("expense_categories", analysis)
        self.assertTrue(analysis["expense_categories"].empty)

    def test_financial_analysis_with_data_matches_the_ui_contract(self):
        transactions = pd.DataFrame([
            {"tx_date": pd.Timestamp("2026-08-01"), "tx_type": "Receita", "value": 1000.0, "category": "Serviços"},
            {"tx_date": pd.Timestamp("2026-08-02"), "tx_type": "Despesa", "value": 250.0, "category": "Materiais"},
        ])
        analysis = financial_analysis(transactions, 2026)
        self.assertEqual(analysis["revenue"], 1000.0)
        self.assertEqual(analysis["expense"], 250.0)
        self.assertEqual(analysis["result"], 750.0)
        self.assertIn("expense_categories", analysis)
        self.assertFalse(analysis["monthly"].empty)

    def test_monthly_closing_exposes_guided_checklist(self):
        closing = monthly_closing(pd.DataFrame(), pd.DataFrame(), [], [], 2026, 8)
        self.assertIn("checklist", closing)
        self.assertEqual(len(closing["checklist"]), 6)
        for item in closing["checklist"]:
            self.assertEqual(set(item), {"Item", "OK", "Detalhe"})

    def test_automatic_obligations_support_all_consuming_screens(self):
        rows = automatic_obligations(2026, today=date(2026, 1, 1))
        self.assertTrue(rows)
        required = {
            "Obrigação", "Competência", "Categoria", "Vencimento",
            "Status automático", "Descrição", "title", "competence",
            "category", "due_date", "status", "details",
        }
        self.assertTrue(required.issubset(rows[0]))


if __name__ == "__main__":
    unittest.main()
