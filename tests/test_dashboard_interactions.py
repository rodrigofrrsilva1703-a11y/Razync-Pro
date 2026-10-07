from pathlib import Path
import unittest


class DashboardInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
        cls.ui = Path("workspace_style.py").read_text(encoding="utf-8")
        cls.assistant = Path("assistant_workspace.py").read_text(encoding="utf-8")
        cls.app = Path("app.py").read_text(encoding="utf-8")

    def test_priority_and_deadline_actions_have_explicit_routes(self):
        self.assertIn('key="dash_primary_next"', self.dashboard)
        self.assertIn('key=f"dashboard_task_open_{index}"', self.dashboard)
        self.assertIn('key=f"dashboard_deadline_open_{index}"', self.dashboard)
        self.assertIn('navigate(task["page"])', self.dashboard)
        self.assertIn('navigate(deadline["page"])', self.dashboard)

    def test_insight_hands_structured_context_to_ai(self):
        self.assertIn("razync_ai_pending_question", self.dashboard)
        self.assertIn("razync_ai_pending_context", self.dashboard)
        self.assertIn('"source": "dashboard_insight"', self.dashboard)
        self.assertIn("Contexto recebido do painel", self.assistant)

    def test_interactive_cards_have_visible_hover_state(self):
        self.assertIn('st-key-rz_metric_card_', self.ui)
        self.assertIn("transform: translateY(-1px)", self.ui)

    def test_dashboard_is_decision_first_and_compact(self):
        self.assertIn("PRÓXIMO PASSO", self.dashboard)
        self.assertIn("Ações rápidas", self.dashboard)
        self.assertIn("Próximos vencimentos", self.dashboard)
        self.assertIn("Ver detalhes e histórico", self.dashboard)

    def test_notification_center_uses_clickable_card_pattern(self):
        self.assertIn("rz_action_card_{level}_notification_", self.app)
        self.assertNotIn('key=f"notification_action_', self.app)


if __name__ == "__main__":
    unittest.main()
