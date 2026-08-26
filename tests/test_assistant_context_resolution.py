from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from assistant_context_resolution import resolve_contextual_question
from product_core import assistant_answer, supports_instant_assistant_answer


def _transactions() -> pd.DataFrame:
    frame = pd.DataFrame([
        {"id": 1, "tx_date": "2026-07-10", "tx_type": "Receita", "description": "Venda julho", "category": "Vendas", "value": 1200.0, "document_number": "", "counterparty": "", "payment_method": "PIX"},
        {"id": 2, "tx_date": "2026-08-10", "tx_type": "Receita", "description": "Venda agosto", "category": "Vendas", "value": 1800.0, "document_number": "", "counterparty": "", "payment_method": "PIX"},
        {"id": 3, "tx_date": "2026-08-12", "tx_type": "Despesa", "description": "Internet", "category": "Serviços", "value": 300.0, "document_number": "", "counterparty": "", "payment_method": "PIX"},
    ])
    frame["tx_date"] = pd.to_datetime(frame["tx_date"])
    return frame


class AssistantContextResolutionTests(unittest.TestCase):
    def test_month_follow_up_reuses_previous_metric(self):
        history = [{"role": "user", "content": "Quanto faturei em julho?"}]
        result = resolve_contextual_question("e agosto?", history, default_year=2026)
        self.assertTrue(result.used_context)
        self.assertEqual(result.confidence, "high")
        self.assertIn("faturamento", result.resolved_question.lower())
        self.assertIn("agosto", result.resolved_question.lower())
        self.assertIn("2026", result.resolved_question)

    def test_compare_follow_up_uses_last_two_months(self):
        history = [
            {"role": "user", "content": "Quanto faturei em julho?"},
            {"role": "assistant", "content": "Em julho..."},
            {"role": "user", "content": "e agosto?"},
        ]
        result = resolve_contextual_question("qual foi melhor?", history, default_year=2026)
        self.assertTrue(result.used_context)
        self.assertIn("julho", result.resolved_question.lower())
        self.assertIn("agosto", result.resolved_question.lower())
        self.assertIn("faturamento", result.resolved_question.lower())

    def test_previous_month_rolls_year_safely(self):
        history = [{"role": "user", "content": "Quanto faturei em janeiro de 2026?"}]
        result = resolve_contextual_question("e o mês anterior?", history, default_year=2026)
        self.assertTrue(result.used_context)
        self.assertIn("dezembro", result.resolved_question.lower())
        self.assertIn("2025", result.resolved_question)

    def test_confirmation_phrase_is_never_rewritten_as_execution(self):
        history = [{"role": "user", "content": "Registre uma despesa de 100 reais"}]
        result = resolve_contextual_question("faz isso", history, default_year=2026)
        self.assertFalse(result.used_context)
        self.assertEqual(result.resolved_question, "faz isso")
        self.assertIn("aprovação", result.reason)

    def test_ambiguous_short_question_stays_unchanged(self):
        history = [{"role": "user", "content": "Como está minha empresa?"}]
        result = resolve_contextual_question("e isso?", history, default_year=2026)
        self.assertFalse(result.used_context)
        self.assertEqual(result.resolved_question, "e isso?")


class ProductCoreContextIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tx = _transactions()
        self.empty_invoices = pd.DataFrame()

    def _answer(self, question: str, history: list[dict]) -> str:
        with patch("product_core._conversation_history", return_value=history):
            return assistant_answer(
                question,
                self.tx,
                self.empty_invoices,
                [],
                81000.0,
                2026,
                obligations=[],
                documents=[],
            )

    def test_august_follow_up_is_answered_locally_with_august_value(self):
        answer = self._answer("e agosto?", [{"role": "user", "content": "Quanto faturei em julho?"}])
        self.assertIn("1.800,00", answer)
        self.assertNotIn("3.000,00", answer)

    def test_which_was_better_compares_july_and_august(self):
        history = [
            {"role": "user", "content": "Quanto faturei em julho?"},
            {"role": "assistant", "content": "R$ 1.200,00"},
            {"role": "user", "content": "e agosto?"},
            {"role": "assistant", "content": "R$ 1.800,00"},
        ]
        answer = self._answer("qual foi melhor?", history)
        self.assertIn("1.200,00", answer)
        self.assertIn("1.800,00", answer)

    def test_contextual_follow_up_is_marked_instant(self):
        history = [{"role": "user", "content": "Quanto faturei em julho?"}]
        with patch("product_core._conversation_history", return_value=history):
            self.assertTrue(supports_instant_assistant_answer("e agosto?"))


if __name__ == "__main__":
    unittest.main()
