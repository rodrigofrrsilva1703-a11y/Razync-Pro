from __future__ import annotations

import unittest
from datetime import date

import pandas as pd

from assistant_query_engine import analyze_business_question, parse_comparison_periods, parse_period


class AssistantQueryEngineTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 8, 21)
        self.transactions = pd.DataFrame([
            {"tx_date": "2026-06-05", "tx_type": "Receita", "description": "Projeto A", "category": "Serviços", "value": 5000.0, "counterparty": "Cliente Alfa", "payment_method": "PIX"},
            {"tx_date": "2026-06-10", "tx_type": "Despesa", "description": "Material", "category": "Materiais", "value": 1200.0, "counterparty": "Fornecedor X", "payment_method": "PIX"},
            {"tx_date": "2026-07-05", "tx_type": "Receita", "description": "Projeto B", "category": "Serviços", "value": 7000.0, "counterparty": "Cliente Beta", "payment_method": "PIX"},
            {"tx_date": "2026-07-12", "tx_type": "Despesa", "description": "Material", "category": "Materiais", "value": 1800.0, "counterparty": "Fornecedor X", "payment_method": "PIX"},
            {"tx_date": "2026-08-03", "tx_type": "Receita", "description": "Projeto C", "category": "Serviços", "value": 8000.0, "counterparty": "Cliente Beta", "payment_method": "PIX"},
            {"tx_date": "2026-08-08", "tx_type": "Despesa", "description": "Anúncios", "category": "Marketing", "value": 2500.0, "counterparty": "Fornecedor Y", "payment_method": "Cartão"},
        ])
        self.transactions["tx_date"] = pd.to_datetime(self.transactions["tx_date"])

    def test_understands_last_three_months(self):
        period = parse_period("Quanto gastei nos últimos 3 meses?", today=self.today)
        self.assertEqual(period.start, date(2026, 6, 1))
        self.assertEqual(period.end, self.today)

    def test_understands_named_month_range(self):
        period = parse_period("Relatório de junho a agosto de 2026", today=self.today)
        self.assertEqual(period.start, date(2026, 6, 1))
        self.assertEqual(period.end, date(2026, 8, 31))

    def test_comparison_between_months(self):
        periods = parse_comparison_periods("Compare julho com agosto", today=self.today)
        self.assertIsNotNone(periods)
        self.assertEqual(periods[0].start, date(2026, 7, 1))
        self.assertEqual(periods[1].start, date(2026, 8, 1))

    def test_answers_expense_total_for_period(self):
        result = analyze_business_question(
            "Quanto gastei nos últimos 3 meses?",
            self.transactions,
            today=self.today,
            default_year=2026,
        )
        self.assertTrue(result.handled)
        self.assertEqual(result.kind, "expense_total")
        self.assertIn("5.500,00", result.summary)

    def test_finds_top_customer_locally(self):
        result = analyze_business_question(
            "Qual cliente mais me pagou este ano?",
            self.transactions,
            today=self.today,
            default_year=2026,
        )
        self.assertTrue(result.handled)
        self.assertIn("Cliente Beta", result.summary)
        self.assertIsNotNone(result.table)

    def test_finds_best_month(self):
        result = analyze_business_question(
            "Qual mês deu mais lucro este ano?",
            self.transactions,
            today=self.today,
            default_year=2026,
        )
        self.assertTrue(result.handled)
        self.assertEqual(result.kind, "monthly_performance")
        self.assertIn("2026-08", result.summary)


if __name__ == "__main__":
    unittest.main()
