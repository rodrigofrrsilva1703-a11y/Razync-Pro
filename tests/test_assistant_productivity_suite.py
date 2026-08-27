from datetime import date, timedelta
import unittest

import pandas as pd

from assistant_response_policy import response_policy_directive
from assistant_workspace import _dynamic_suggestions, _pending_overview, _trace_caption


class AssistantProductivitySuiteTests(unittest.TestCase):
    def test_question_suggestions_adapt_to_business_state(self):
        rows = pd.DataFrame([
            {"tx_date": pd.Timestamp("2026-08-01"), "tx_type": "Receita", "value": 100.0, "document_number": ""}
        ])
        suggestions = _dynamic_suggestions(
            mode="Perguntar", profile={}, transactions=rows, das_rows=[{"status": "Pendente"}],
            obligations=[{"status": "Pendente"}], documents=[], annual_limit=81000.0, current_year=2026,
        )
        labels = [label for label, _ in suggestions]
        self.assertIn("Revisar DAS", labels)
        self.assertIn("Obrigações", labels)

    def test_action_mode_prioritizes_missing_setup_and_documents(self):
        suggestions = _dynamic_suggestions(
            mode="Fazer", profile={}, transactions=pd.DataFrame(), das_rows=[], obligations=[],
            documents=[], annual_limit=81000.0, current_year=2026,
        )
        labels = [label for label, _ in suggestions]
        self.assertEqual(labels[0], "Completar meu MEI")
        self.assertIn("Organizar documentos", labels)

    def test_pending_overview_is_deterministic_and_actionable(self):
        yesterday = date.today() - timedelta(days=1)
        rows = pd.DataFrame([{"document_number": ""}, {"document_number": "NF-1"}])
        items = _pending_overview(
            profile={}, transactions=rows,
            das_rows=[{"status": "Pendente", "due_date": yesterday}],
            obligations=[{"status": "Pendente", "due_date": yesterday}],
            documents=[], current_year=date.today().year,
        )
        titles = [title for title, _, _ in items]
        self.assertIn("Cadastro do MEI", titles)
        self.assertIn("DAS", titles)
        self.assertIn("Obrigações", titles)
        self.assertIn("Documentos", titles)

    def test_trace_exposes_source_model_period_and_latency(self):
        trace = _trace_caption({"provider": "Local", "model": "Razync local"}, current_year=2026, elapsed=.42)
        self.assertIn("Fonte: Local", trace)
        self.assertIn("2026", trace)
        self.assertIn("0.4s", trace)

    def test_external_response_policy_requires_evidence_and_next_step(self):
        directive = response_policy_directive()
        self.assertIn("evidências encontradas", directive)
        self.assertIn("próximo passo recomendado", directive)
        self.assertIn("não invente evidências", directive)


if __name__ == "__main__":
    unittest.main()
