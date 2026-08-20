from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from assistant_actions import AssistantActionError, execute_assistant_action, plan_assistant_action


class AssistantActionPlanningTests(unittest.TestCase):
    def test_plans_expense_from_natural_portuguese(self):
        draft = plan_assistant_action(
            "Registre uma despesa de R$ 89,90 com material hoje no PIX",
            today=date(2026, 8, 20),
        )
        self.assertIsNotNone(draft)
        self.assertTrue(draft.ready)
        self.assertEqual(draft.action_type, "transaction")
        self.assertEqual(draft.payload["tx_type"], "Despesa")
        self.assertEqual(draft.payload["value"], 89.90)
        self.assertEqual(draft.payload["category"], "Materiais")
        self.assertEqual(draft.payload["payment_method"], "PIX")
        self.assertEqual(draft.payload["tx_date"], "2026-08-20")

    def test_plans_revenue_for_yesterday(self):
        draft = plan_assistant_action(
            "Lance uma receita de 1500 referente a serviço ontem por PIX",
            today=date(2026, 8, 20),
        )
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["tx_type"], "Receita")
        self.assertEqual(draft.payload["tx_date"], "2026-08-19")
        self.assertEqual(draft.payload["category"], "Serviços")

    def test_understands_colloquial_expense_command(self):
        draft = plan_assistant_action(
            "Coloca uma despesa de 42 reais com almoço hoje",
            today=date(2026, 8, 20),
        )
        self.assertIsNotNone(draft)
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["tx_type"], "Despesa")
        self.assertEqual(draft.payload["value"], 42.0)
        self.assertEqual(draft.payload["description"], "almoço")

    def test_understands_create_revenue_command(self):
        draft = plan_assistant_action(
            "Cria um lançamento de receita de R$ 250 por serviço no pix",
            today=date(2026, 8, 20),
        )
        self.assertIsNotNone(draft)
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["tx_type"], "Receita")
        self.assertEqual(draft.payload["payment_method"], "PIX")

    def test_understands_short_invoice_name(self):
        draft = plan_assistant_action(
            "Cadastra a NF-e 88 no valor de R$ 300 referente a instalação",
            today=date(2026, 8, 20),
        )
        self.assertIsNotNone(draft)
        self.assertEqual(draft.action_type, "invoice")
        self.assertTrue(draft.ready)

    def test_plans_invoice_without_confusing_number_with_amount(self):
        draft = plan_assistant_action(
            "Cadastre a nota 123 do cliente Ana no valor de R$ 1.500,00 referente a consultoria",
            today=date(2026, 8, 20),
        )
        self.assertTrue(draft.ready)
        self.assertEqual(draft.action_type, "invoice")
        self.assertEqual(draft.payload["number"], "123")
        self.assertEqual(draft.payload["amount"], 1500.0)
        self.assertEqual(draft.payload["customer"], "Ana")
        self.assertIn("consultoria", draft.payload["description"])

    def test_guidance_question_does_not_create_action(self):
        self.assertIsNone(plan_assistant_action("Como cadastrar uma receita?", today=date(2026, 8, 20)))

    def test_missing_amount_requires_more_information(self):
        draft = plan_assistant_action("Registre uma despesa de aluguel hoje", today=date(2026, 8, 20))
        self.assertFalse(draft.ready)
        self.assertIn("valor", draft.missing_fields)

    @patch("database.add_transaction")
    def test_executes_only_confirmed_validated_transaction(self, add_transaction):
        draft = plan_assistant_action(
            "Registre uma despesa de R$ 25,00 com transporte hoje no PIX",
            today=date.today(),
        )
        message = execute_assistant_action(7, draft.to_dict())
        self.assertIn("salvo", message.lower())
        add_transaction.assert_called_once()

    def test_rejects_incomplete_action(self):
        draft = plan_assistant_action("Registre uma despesa de aluguel hoje", today=date.today())
        with self.assertRaises(AssistantActionError):
            execute_assistant_action(7, draft.to_dict())


if __name__ == "__main__":
    unittest.main()

