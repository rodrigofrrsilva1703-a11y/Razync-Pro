import unittest
from datetime import date

import pandas as pd

from automation_tools import financial_projection, next_recurrence_date, upcoming_deadlines
from product_core import assistant_answer


class AutomationToolsTests(unittest.TestCase):
    def test_monthly_recurrence_handles_short_months_and_year_change(self):
        self.assertEqual(next_recurrence_date(date(2026, 1, 31), "Mensal"), date(2026, 2, 28))
        self.assertEqual(next_recurrence_date(date(2026, 12, 15), "Mensal"), date(2027, 1, 15))
        self.assertEqual(next_recurrence_date(date(2024, 2, 29), "Anual"), date(2025, 2, 28))
        self.assertEqual(next_recurrence_date(date(2026, 8, 14), "Semanal"), date(2026, 8, 21))

    def test_projection_warns_before_the_mei_limit_is_exceeded(self):
        frame = pd.DataFrame(
            [
                {"tx_date": pd.Timestamp("2026-01-10"), "tx_type": "Receita", "value": 50000.0},
                {"tx_date": pd.Timestamp("2026-02-10"), "tx_type": "Despesa", "value": 10000.0},
            ]
        )
        result = financial_projection(frame, 81000.0, 2026, date(2026, 6, 1))
        self.assertEqual(result["projected_revenue"], 100000.0)
        self.assertEqual(result["projected_result"], 80000.0)
        self.assertTrue(result["limit_risk"])

    def test_upcoming_deadlines_unifies_das_and_obligations(self):
        rows = upcoming_deadlines(
            [{"competence": "2026-08", "due_date": date(2026, 8, 20), "status": "Pendente"}],
            [{"title": "Enviar documento", "due_date": date(2026, 8, 18), "status": "Pendente"}],
            today=date(2026, 8, 14),
            days=10,
        )
        self.assertEqual([item["title"] for item in rows], ["Enviar documento", "DAS 2026-08"])

    def test_assistant_answers_new_business_questions(self):
        frame = pd.DataFrame(
            [
                {"tx_date": pd.Timestamp("2026-08-02"), "tx_type": "Receita", "value": 3000.0, "description": "Projeto", "category": "Serviços", "document_number": ""},
                {"tx_date": pd.Timestamp("2026-08-03"), "tx_type": "Despesa", "value": 900.0, "description": "Equipamento", "category": "Materiais", "document_number": "NF-1"},
                {"tx_date": pd.Timestamp("2026-07-02"), "tx_type": "Receita", "value": 2000.0, "description": "Projeto anterior", "category": "Serviços", "document_number": "NF-2"},
            ]
        )
        empty_invoices = pd.DataFrame()
        today = date(2026, 8, 14)

        comparison = assistant_answer("Compare este mês com o anterior", frame, empty_invoices, [], 81000, 2026, today=today)
        biggest = assistant_answer("Qual foi minha maior despesa?", frame, empty_invoices, [], 81000, 2026, today=today)
        missing = assistant_answer("Tenho documentos faltando?", frame, empty_invoices, [], 81000, 2026, documents=[], today=today)

        self.assertIn("R$ 1.000,00 a mais", comparison)
        self.assertIn("Equipamento", biggest)
        self.assertIn("1 lançamento", missing)


if __name__ == "__main__":
    unittest.main()
