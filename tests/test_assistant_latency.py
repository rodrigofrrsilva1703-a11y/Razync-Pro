from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

import assistant_workspace as workspace


def _transactions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "id": 1,
            "tx_date": pd.Timestamp("2026-08-10"),
            "tx_type": "Despesa",
            "description": "Internet",
            "category": "Serviços",
            "value": 120.0,
            "document_number": "",
            "counterparty": "",
            "payment_method": "PIX",
        }
    ])


class AssistantLatencyTests(unittest.TestCase):
    def _answer(self, question: str) -> dict:
        return workspace._answer_question(
            question,
            profile={},
            transactions=_transactions(),
            invoices=pd.DataFrame(),
            das_rows=[],
            obligations=[],
            documents=[],
            annual_limit=81000.0,
            current_year=2026,
            current_page="Assistente Razync",
        )

    def test_common_business_query_avoids_quota_and_external_provider(self):
        provider = {
            "ai_enabled": True,
            "openai_enabled": True,
            "gemini_enabled": False,
            "openai_api_key": "test",
            "openai_model": "test-model",
            "gemini_api_key": "",
            "gemini_model": "",
            "model": "test-model",
        }
        with (
            patch.object(workspace, "st", SimpleNamespace(session_state={})),
            patch.object(workspace, "_provider_state", return_value=provider),
            patch.object(workspace, "_current_user_id", return_value=7),
            patch.object(workspace, "_cached_ai_usage", side_effect=AssertionError("quota should not be queried")),
            patch.object(workspace, "reserve_ai_request", side_effect=AssertionError("provider should not be reserved")),
        ):
            result = self._answer("Quanto gastei em agosto de 2026?")

        self.assertEqual(result["provider"], "Análise instantânea")
        self.assertIn("R$ 120,00", result["answer"])

    def test_simple_transaction_is_prepared_without_external_ai(self):
        provider = {
            "ai_enabled": True,
            "openai_enabled": True,
            "gemini_enabled": False,
            "openai_api_key": "test",
            "openai_model": "test-model",
            "gemini_api_key": "",
            "gemini_model": "",
            "model": "test-model",
        }
        session = {}
        with (
            patch.object(workspace, "st", SimpleNamespace(session_state=session)),
            patch.object(workspace, "_provider_state", return_value=provider),
            patch.object(workspace, "_current_user_id", return_value=None),
            patch.object(workspace, "reserve_ai_request", side_effect=AssertionError("provider should not be reserved")),
        ):
            result = self._answer("Recebi R$ 500 por um serviço via PIX")

        self.assertEqual(result["provider"], "Local")
        self.assertEqual(result["action"]["payload"]["value"], 500.0)
        self.assertTrue(result["action"]["ready"])


if __name__ == "__main__":
    unittest.main()
