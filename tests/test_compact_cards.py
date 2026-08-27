from pathlib import Path
import unittest


class CompactCardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compact = Path("compact_cards.py").read_text(encoding="utf-8")
        cls.dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
        cls.finance = Path("finance_workspace.py").read_text(encoding="utf-8")
        cls.fiscal = Path("fiscal_workspace.py").read_text(encoding="utf-8")

    def test_metric_cards_are_compact(self):
        self.assertIn('min-height: 82px !important', self.compact)
        self.assertIn('[class*="st-key-rz_metric_card_"] button', self.compact)
        self.assertNotIn('min-height:112px', self.compact)

    def test_primary_workspaces_use_compact_card_layer(self):
        for source in (self.dashboard, self.finance, self.fiscal):
            self.assertIn('inject_compact_cards()', source)
            self.assertIn('metric_card(', source)

    def test_clickable_cards_have_meaningful_destinations(self):
        self.assertIn('navigate("Financeiro")', self.dashboard)
        self.assertIn('navigate("Fiscal")', self.dashboard)
        self.assertIn('navigate("Conciliação")', self.finance)
        self.assertIn('navigate("DAS")', self.fiscal)
        self.assertIn('navigate("Documentos")', self.fiscal)

    def test_clicks_do_not_execute_destructive_actions(self):
        for source in (self.dashboard, self.finance, self.fiscal):
            self.assertNotIn('delete_', source)
            self.assertNotIn('confirm_action(', source)


if __name__ == "__main__":
    unittest.main()
