from pathlib import Path
import unittest


class DashboardInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
        cls.ui = Path("ui_system.py").read_text(encoding="utf-8")
        cls.assistant = Path("assistant_workspace.py").read_text(encoding="utf-8")
        cls.app = Path("app.py").read_text(encoding="utf-8")

    def test_priority_and_deadline_cards_are_full_surface_actions(self):
        self.assertIn("def _action_card", self.dashboard)
        self.assertIn('key=f"priority_{idx}"', self.dashboard)
        self.assertIn('key=f"deadline_{idx}"', self.dashboard)
        self.assertNotIn('st.button("Resolver", key=f"dashv2_action_', self.dashboard)

    def test_insight_hands_structured_context_to_ai(self):
        self.assertIn('razync_ai_pending_question', self.dashboard)
        self.assertIn('razync_ai_pending_context', self.dashboard)
        self.assertIn('"source": "dashboard_insight"', self.dashboard)
        self.assertIn('Contexto recebido do painel', self.assistant)

    def test_action_cards_have_visible_interaction_states(self):
        self.assertIn('st-key-rz_action_card_', self.ui)
        self.assertIn('transform:translateY(-2px)', self.ui)

    def test_notification_center_uses_the_same_clickable_card_pattern(self):
        self.assertIn('rz_action_card_{level}_notification_', self.app)
        self.assertNotIn('key=f"notification_action_', self.app)


if __name__ == "__main__":
    unittest.main()
