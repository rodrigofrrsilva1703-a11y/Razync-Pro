from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

import assistant_workspace as workspace


class AssistantSessionRegressionTests(unittest.TestCase):
    def test_current_user_id_reads_authenticated_session(self):
        with patch.object(workspace, "st", SimpleNamespace(session_state={"user": {"id": 42}})):
            self.assertEqual(workspace._current_user_id(), 42)

    def test_current_user_id_rejects_missing_or_invalid_identity(self):
        cases = [
            {},
            {"user": None},
            {"user": {"id": None}},
            {"user": {"id": "invalid"}},
            {"user": {"id": 0}},
            {"user": {"id": -1}},
        ]
        for session_state in cases:
            with self.subTest(session_state=session_state):
                with patch.object(workspace, "st", SimpleNamespace(session_state=session_state)):
                    self.assertIsNone(workspace._current_user_id())

    def test_authenticated_user_can_reach_external_provider_path(self):
        provider = {
            "ai_enabled": True,
            "openai_enabled": False,
            "gemini_enabled": True,
            "openai_api_key": "",
            "openai_model": "",
            "gemini_api_key": "test-key",
            "gemini_model": "test-model",
            "model": "test-model",
        }
        session = {
            "user": {"id": 7},
            "razync_ai_messages": [{"role": "assistant", "content": "Olá"}],
            "razync_ai_history_loaded_for": 7,
        }
        with (
            patch.object(workspace, "st", SimpleNamespace(session_state=session)),
            patch.object(workspace, "_provider_state", return_value=provider),
            patch.object(workspace, "_daily_request_limit", return_value=20),
            patch.object(workspace, "_cached_ai_usage", return_value=0),
            patch.object(workspace, "reserve_ai_request", return_value=(True, 1)),
            patch.object(workspace, "plan_record_operation", return_value=None),
            patch.object(workspace, "plan_assistant_action", return_value=None),
            patch.object(workspace, "answer_record_search", return_value=None),
            patch.object(workspace, "analyze_business_question", return_value=SimpleNamespace(handled=False, summary="")),
            patch.object(workspace, "supports_instant_assistant_answer", return_value=False),
            patch.object(workspace, "build_safe_business_context", return_value={}),
            patch.object(workspace, "build_product_context", return_value={}),
            patch.object(workspace, "run_provider_chain", return_value=("Resposta externa", "Gemini", ())) as provider_chain,
        ):
            result = workspace._answer_question(
                "Explique meu cenário de forma detalhada",
                profile={},
                transactions=pd.DataFrame(),
                invoices=pd.DataFrame(),
                das_rows=[],
                obligations=[],
                documents=[],
                annual_limit=81000.0,
                current_year=2026,
                current_page="Assistente Razync",
            )

        self.assertEqual(result["provider"], "Gemini")
        provider_chain.assert_called_once()

    def test_resource_bundle_receives_authenticated_user_id(self):
        session = {"user": {"id": 9}}
        expected = {
            "route": "Documentos",
            "route_label": "Abrir Documentos",
            "downloads": [],
            "note": None,
        }
        with (
            patch.object(workspace, "st", SimpleNamespace(session_state=session)),
            patch.object(workspace, "should_prepare_resources", return_value=True),
            patch.object(workspace, "build_resource_bundle", return_value=expected) as bundle,
        ):
            result = workspace._prepare_resources(
                "Quero meus documentos",
                profile={},
                transactions=pd.DataFrame(),
                invoices=pd.DataFrame(),
                das_rows=[],
                obligations=[],
                documents=[],
                current_year=2026,
            )

        self.assertEqual(result, expected)
        self.assertEqual(bundle.call_args.kwargs["user_id"], 9)


if __name__ == "__main__":
    unittest.main()
