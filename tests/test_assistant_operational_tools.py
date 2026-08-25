from __future__ import annotations

import unittest
from datetime import date

import pandas as pd

from assistant_operational_tools import (
    answer_record_search, plan_record_operation, proactive_answer, search_business_records,
)


class AssistantOperationalToolsTests(unittest.TestCase):
    def setUp(self):
        self.transactions = pd.DataFrame([
            {"id": 1, "tx_date": date(2026, 8, 23), "tx_type": "Despesa", "description": "Internet", "category": "Outros", "value": 100.0, "document_number": "", "counterparty": "Operadora", "payment_method": "PIX"},
            {"id": 2, "tx_date": date(2026, 8, 20), "tx_type": "Receita", "description": "Consultoria Ana", "category": "Serviços", "value": 500.0, "document_number": "", "counterparty": "Ana", "payment_method": "PIX"},
        ])
        self.invoices = pd.DataFrame([
            {"id": 9, "issue_date": date(2026, 8, 20), "number": "NF-9", "customer": "Ana", "description": "Consultoria", "amount": 500.0, "status": "Emitida"},
        ])

    def test_searches_across_records_locally(self):
        rows = search_business_records(
            "procure Ana", transactions=self.transactions, invoices=self.invoices,
            das_rows=[], obligations=[], documents=[],
        )
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[0]["score"], 1)

    def test_answers_search_with_explainability(self):
        result = answer_record_search(
            "Procure internet", transactions=self.transactions, invoices=self.invoices,
            das_rows=[], obligations=[], documents=[],
        )
        self.assertIn("Internet", result["answer"])
        self.assertEqual(result["confidence"], "Alta")

    def test_prepares_exact_transaction_update(self):
        draft = plan_record_operation(
            "Altere a despesa de internet de 100 para 120",
            transactions=self.transactions, invoices=self.invoices, obligations=[], today=date(2026, 8, 24),
        )
        self.assertIsNotNone(draft)
        self.assertEqual(draft.action_type, "update_transaction")
        self.assertEqual(draft.payload["record_id"], 1)
        self.assertEqual(draft.payload["updates"]["value"], 120.0)

    def test_prepares_invoice_reconciliation_with_score(self):
        draft = plan_record_operation(
            "Concilie a nota NF-9",
            transactions=self.transactions, invoices=self.invoices, obligations=[], today=date(2026, 8, 24),
        )
        self.assertIsNotNone(draft)
        self.assertEqual(draft.action_type, "reconcile_invoice")
        self.assertGreaterEqual(draft.payload["score"], 45)

    def test_proactive_summary_includes_operational_signals(self):
        result = proactive_answer(
            transactions=self.transactions, invoices=self.invoices,
            obligations=[{"status": "Pendente"}], das_rows=[{"status": "Pendente"}],
            today=date(2026, 8, 24),
        )
        self.assertIn("DAS", result["answer"])
        self.assertIn("conciliação", result["answer"])


if __name__ == "__main__":
    unittest.main()
