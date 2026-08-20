from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

import pandas as pd

from ai_assistant import (
    ask_razync_ai,
    build_safe_business_context,
    build_safe_conversation_history,
)


class _FakeResponse:
    output_text = "Resposta segura"


class _FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponse()


class _FakeClient:
    last = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.responses = _FakeResponses()
        _FakeClient.last = self


class RazyncAIContextTests(unittest.TestCase):
    def test_context_is_aggregate_and_excludes_direct_identifiers(self):
        tx = pd.DataFrame(
            [
                {
                    "tx_date": pd.Timestamp("2026-08-01"),
                    "tx_type": "Receita",
                    "description": "Cliente Secreto LTDA",
                    "category": "Serviços",
                    "value": 1500.0,
                    "document_number": "NF-123",
                    "counterparty": "Fulano",
                },
                {
                    "tx_date": pd.Timestamp("2026-08-02"),
                    "tx_type": "Despesa",
                    "description": "Fornecedor Confidencial",
                    "category": "Materiais",
                    "value": 300.0,
                    "document_number": "",
                    "counterparty": "Beltrano",
                },
            ]
        )
        invoices = pd.DataFrame(
            [{"number": "NF-123", "amount": 1500.0, "status": "Emitida", "customer": "Cliente Secreto LTDA"}]
        )
        context = build_safe_business_context(
            profile={
                "cnpj": "12.345.678/0001-90",
                "business_name": "Empresa Sigilosa",
                "phone": "11999999999",
                "activity_type": "Serviços",
                "opening_date": "2025-01-01",
            },
            transactions=tx,
            invoices=invoices,
            das_rows=[],
            obligations=[],
            documents=[{"filename": "documento-secreto.pdf", "category": "DAS"}],
            annual_limit=81000.0,
            year=2026,
            today=date(2026, 8, 18),
        )
        rendered = str(context)
        for secret in (
            "12.345.678/0001-90",
            "Empresa Sigilosa",
            "11999999999",
            "Cliente Secreto LTDA",
            "Fornecedor Confidencial",
            "Fulano",
            "Beltrano",
            "documento-secreto.pdf",
            "NF-123",
        ):
            self.assertNotIn(secret, rendered)
        self.assertEqual(context["financial"]["revenue"], 1500.0)
        self.assertEqual(context["financial"]["expense"], 300.0)
        self.assertFalse(context["privacy"]["direct_identifiers_included"])

    def test_context_adds_comparative_business_metrics(self):
        tx = pd.DataFrame(
            [
                {"tx_date": pd.Timestamp("2026-07-10"), "tx_type": "Receita", "category": "Serviços", "value": 1000.0, "document_number": ""},
                {"tx_date": pd.Timestamp("2026-07-11"), "tx_type": "Despesa", "category": "Materiais", "value": 200.0, "document_number": ""},
                {"tx_date": pd.Timestamp("2026-08-10"), "tx_type": "Receita", "category": "Serviços", "value": 1500.0, "document_number": ""},
                {"tx_date": pd.Timestamp("2026-08-11"), "tx_type": "Despesa", "category": "Materiais", "value": 400.0, "document_number": ""},
            ]
        )
        context = build_safe_business_context(
            profile={}, transactions=tx, invoices=pd.DataFrame(), das_rows=[], obligations=[], documents=[],
            annual_limit=81000.0, year=2026, today=date(2026, 8, 20),
        )
        financial = context["financial"]
        self.assertEqual(financial["current_month"]["revenue"], 1500.0)
        self.assertEqual(financial["previous_month"]["revenue"], 1000.0)
        self.assertEqual(financial["month_over_month"]["revenue_change_percent"], 50.0)
        self.assertIn("projected_revenue", financial)
        self.assertIn("margin_percent", financial)

    def test_conversation_memory_redacts_common_identifiers(self):
        history = build_safe_conversation_history(
            [
                {"role": "user", "content": "Meu CPF é 123.456.789-00 e email teste@exemplo.com"},
                {"role": "assistant", "content": "Entendi. Vamos continuar."},
            ]
        )
        rendered = str(history)
        self.assertNotIn("123.456.789-00", rendered)
        self.assertNotIn("teste@exemplo.com", rendered)
        self.assertIn("[CPF removido]", rendered)
        self.assertIn("[email removido]", rendered)

    @patch("ai_assistant.OpenAI", _FakeClient)
    def test_openai_request_disables_storage(self):
        answer = ask_razync_ai(
            "Como estou?",
            context={"financial": {"revenue": 1000.0}},
            api_key="test-key",
            model="gpt-5.6-luna",
            conversation=[{"role": "user", "content": "E no mês passado?"}],
        )
        self.assertEqual(answer, "Resposta segura")
        self.assertIsNotNone(_FakeClient.last)
        self.assertFalse(_FakeClient.last.responses.kwargs["store"])
        self.assertEqual(_FakeClient.last.responses.kwargs["model"], "gpt-5.6-luna")
        self.assertEqual(_FakeClient.last.responses.kwargs["max_output_tokens"], 1100)


if __name__ == "__main__":
    unittest.main()
