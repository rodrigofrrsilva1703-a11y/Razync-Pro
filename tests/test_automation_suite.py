from datetime import date
import unittest
from unittest.mock import patch

import pandas as pd

from automation_suite import automation_overview, cash_forecast, das_payment_matches, expense_anomalies, learned_category, receivable_reminders


class AutomationSuiteTests(unittest.TestCase):
    def test_learns_category_from_similar_history(self):
        history = pd.DataFrame([{"description": "Conta de internet fibra", "category": "Internet", "tx_type": "Despesa"}])
        result = learned_category("Conta internet fibra agosto", "Despesa", history, "Fornecedores")
        self.assertEqual(result["category"], "Internet")
        self.assertIn(result["confidence"], {"Alta", "Média"})

    def test_matches_probable_das_payment(self):
        tx = pd.DataFrame([{"id": 1, "tx_date": pd.Timestamp("2026-08-20"), "tx_type": "Despesa", "description": "Pagamento DAS MEI", "value": 80.90}])
        matches = das_payment_matches([{"id": 4, "competence": "2026-07", "due_date": date(2026, 8, 20), "amount": 80.90, "status": "Pendente"}], tx)
        self.assertEqual(matches[0]["transaction_id"], 1)
        self.assertGreaterEqual(matches[0]["score"], 90)

    def test_forecast_projects_three_months(self):
        tx = pd.DataFrame([{"tx_date": pd.Timestamp("2026-08-01"), "tx_type": "Receita", "value": 3000.0}, {"tx_date": pd.Timestamp("2026-08-02"), "tx_type": "Despesa", "value": 1200.0}])
        result = cash_forecast(tx, 3, today=date(2026, 8, 15))
        self.assertEqual(len(result), 3)
        self.assertGreater(result.iloc[-1]["Saldo projetado"], 0)

    def test_anomaly_requires_history(self):
        tx = pd.DataFrame([
            {"id": 1, "tx_date": pd.Timestamp("2026-01-01"), "tx_type": "Despesa", "description": "A", "category": "Taxas", "value": 100},
            {"id": 2, "tx_date": pd.Timestamp("2026-02-01"), "tx_type": "Despesa", "description": "B", "category": "Taxas", "value": 110},
            {"id": 3, "tx_date": pd.Timestamp("2026-03-01"), "tx_type": "Despesa", "description": "C", "category": "Taxas", "value": 900},
        ])
        self.assertEqual(expense_anomalies(tx, 2026)[0]["id"], 3)

    def test_creates_reminder_without_sending_it(self):
        invoices = pd.DataFrame([{"id": 7, "number": "N-7", "customer": "Cliente", "amount": 500, "status": "Emitida"}])
        reminders = receivable_reminders(invoices, pd.DataFrame())
        self.assertEqual(len(reminders), 1)
        self.assertTrue(reminders[0]["whatsapp_url"].startswith("https://wa.me/"))


    def test_overview_exposes_sorted_actionable_routes(self):
        with (
            patch("automation_suite.monthly_closing", return_value={"score": 100, "checklist": []}),
            patch("automation_suite.smart_invoice_matches", return_value=pd.DataFrame()),
            patch("automation_suite.das_payment_matches", return_value=[]),
            patch("automation_suite.expense_anomalies", return_value=[]),
            patch("automation_suite.document_queue", return_value={"missing_count": 0}),
            patch("automation_suite.receivable_reminders", return_value=[]),
            patch("automation_suite.cash_forecast", return_value=pd.DataFrame()),
        ):
            result = automation_overview(
                {}, pd.DataFrame(), pd.DataFrame(), [], [
                    {"status": "Pendente", "due_date": date(2026, 1, 10)}
                ], [], 2026, 8,
            )

        self.assertEqual(result["action_items"][0]["priority"], 1)
        self.assertEqual(result["action_items"][0]["page"], "Obrigações")
        self.assertIn("actions", result)



if __name__ == "__main__":
    unittest.main()

