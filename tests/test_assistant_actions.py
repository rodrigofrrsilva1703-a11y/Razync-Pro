from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from assistant_actions import (
    AssistantActionError, execute_assistant_action, plan_assistant_action,
    plan_document_action, revise_action_draft, undo_assistant_action,
)


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

    def test_plans_monthly_recurring_expense(self):
        draft = plan_assistant_action(
            "Registre uma despesa mensal de R$ 950 de aluguel no PIX",
            today=date(2026, 8, 20),
        )
        self.assertEqual(draft.action_type, "recurring_transaction")
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["frequency"], "Mensal")

    def test_plans_obligation_reminder(self):
        draft = plan_assistant_action(
            "Me lembre de pagar o DAS em 25/08/2026",
            today=date(2026, 8, 20),
        )
        self.assertEqual(draft.action_type, "obligation")
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["due_date"], "2026-08-25")

    def test_plans_customer_contact(self):
        draft = plan_assistant_action(
            "Cadastre o cliente Maria email maria@example.com telefone 11999998888",
            today=date(2026, 8, 20),
        )
        self.assertEqual(draft.action_type, "contact")
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["name"], "Maria")

    def test_revises_incomplete_draft_with_user_value(self):
        draft = plan_assistant_action("Registre uma despesa de aluguel", today=date(2026, 8, 20))
        revised = revise_action_draft(draft.to_dict(), {"value": 900})
        self.assertTrue(revised.ready)
        self.assertEqual(revised.payload["value"], 900)
        self.assertEqual(revised.action_key, draft.action_key)

    def test_prepares_invoice_from_document_analysis(self):
        draft = plan_document_action(
            {"category": "Nota Fiscal", "value": 780.5, "document_number": "NF123"},
            "nota.pdf", today=date(2026, 8, 20),
        )
        self.assertEqual(draft.action_type, "invoice")
        self.assertTrue(draft.ready)
        self.assertEqual(draft.payload["amount"], 780.5)

    def test_prepares_multiple_expenses_as_one_confirmable_batch(self):
        draft = plan_assistant_action(
            "Registre três despesas: aluguel 900, internet 120 e energia 180",
            today=date(2026, 8, 20),
        )
        self.assertIsNotNone(draft)
        self.assertEqual(draft.action_type, "batch")
        self.assertTrue(draft.ready)
        self.assertEqual(len(draft.payload["items"]), 3)
        self.assertIn("1,200.00", draft.summary)

    @patch("assistant_action_store.complete_action")
    @patch("assistant_action_store.claim_action")
    @patch("assistant_actions._execute_one")
    def test_executes_batch_and_returns_one_receipt(self, execute_one, claim_action, complete_action):
        claim_action.return_value = (True, None)
        execute_one.side_effect = [
            {"message": "ok", "action_type": "transaction", "record_id": 1},
            {"message": "ok", "action_type": "transaction", "record_id": 2},
        ]
        draft = {
            "action_type": "batch", "action_key": "batch-1", "channel": "web",
            "summary": "2 lançamentos", "missing_fields": [],
            "payload": {"items": [{"action_type": "transaction"}, {"action_type": "transaction"}]},
        }
        receipt = execute_assistant_action(7, draft, return_receipt=True)
        self.assertEqual(receipt["action_type"], "batch")
        self.assertEqual(len(receipt["items"]), 2)
        complete_action.assert_called_once()

    @patch("assistant_action_store.claim_action")
    def test_repeated_confirmation_returns_existing_receipt(self, claim_action):
        claim_action.return_value = (False, {"message": "salvo", "action_type": "transaction", "record_id": 9})
        receipt = execute_assistant_action(7, {
            "action_type": "transaction", "action_key": "same", "channel": "web",
            "summary": "Despesa", "missing_fields": [], "payload": {},
        }, return_receipt=True)
        self.assertTrue(receipt["duplicate"])
        self.assertIn("duplicado", receipt["message"].lower())

    @patch("database.delete_transaction")
    def test_undoes_exact_assistant_transaction(self, delete_transaction):
        message = undo_assistant_action(7, {"action_type": "transaction", "record_id": 42})
        self.assertIn("desfeita", message)
        delete_transaction.assert_called_once_with(7, 42)


if __name__ == "__main__":
    unittest.main()

