from pathlib import Path
import unittest


class DashboardInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
        cls.ui = Path("workspace_style.py").read_text(encoding="utf-8")
        cls.app = Path("app.py").read_text(encoding="utf-8")

    def test_dashboard_keeps_one_primary_next_action(self):
        self.assertIn('key="dash_primary_next"', self.dashboard)
        self.assertIn('navigate(task["page"])', self.dashboard)
        self.assertNotIn('key=f"dashboard_task_open_{index}"', self.dashboard)
        self.assertNotIn('key=f"dashboard_deadline_open_{index}"', self.dashboard)

    def test_dashboard_does_not_duplicate_floating_ai_actions(self):
        self.assertNotIn("razync_ai_pending_question", self.dashboard)
        self.assertNotIn("Explicar com IA", self.dashboard)

    def test_kpis_are_informational_not_full_surface_actions(self):
        self.assertIn(".rz-stat-card", self.ui)
        self.assertIn("stat_card(", self.dashboard)
        self.assertNotIn("metric_card(", self.dashboard)

    def test_dashboard_is_editorial_and_decision_first(self):
        self.assertIn("O QUE MERECE ATENÇÃO AGORA", self.dashboard)
        self.assertIn("＋ Movimentação", self.dashboard)
        self.assertIn("PRÓXIMOS VENCIMENTOS", self.dashboard)
        self.assertIn('st.expander("Mais contexto")', self.dashboard)

    def test_notification_center_keeps_actionable_alerts(self):
        self.assertIn("rz_action_card_{level}_notification_", self.app)
        self.assertNotIn('key=f"notification_action_', self.app)


if __name__ == "__main__":
    unittest.main()
