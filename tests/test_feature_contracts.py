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
