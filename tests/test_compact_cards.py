from pathlib import Path
import unittest


class CompactCardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compact = Path("compact_cards.py").read_text(encoding="utf-8")
        cls.workspace = Path("workspace_style.py").read_text(encoding="utf-8")
        cls.dashboard = Path("dashboard_workspace.py").read_text(encoding="utf-8")
        cls.finance = Path("finance_workspace.py").read_text(encoding="utf-8")
        cls.fiscal = Path("fiscal_workspace.py").read_text(encoding="utf-8")
        cls.app = Path("app.py").read_text(encoding="utf-8")
        cls.account = Path("account_workspace.py").read_text(encoding="utf-8")
        cls.productivity = Path("productivity_workspace.py").read_text(encoding="utf-8")

    def test_kpis_are_quiet_and_not_buttons(self):
        self.assertIn("def stat_card", self.compact)
        self.assertIn(".rz-stat-card", self.workspace)
        for source in (self.dashboard, self.finance, self.fiscal):
            self.assertIn("stat_card(", source)
            self.assertNotIn("metric_card(", source)

    def test_primary_workspaces_keep_secondary_information_collapsed(self):
        self.assertIn('st.expander("Planejamento e ferramentas")', self.finance)
        self.assertIn('st.expander("Relatórios e ferramentas")', self.fiscal)

    def test_main_actions_remain_meaningful(self):
        self.assertIn('navigate("Movimentações")', self.dashboard)
        self.assertIn('navigate("Importar Extrato")', self.dashboard)
        self.assertIn('navigate("Conciliação")', self.finance)
        self.assertIn('navigate("DAS")', self.fiscal)
        self.assertIn('navigate("Documentos")', self.fiscal)

    def test_clicks_do_not_execute_destructive_actions(self):
        for source in (self.dashboard, self.finance, self.fiscal):
            self.assertNotIn("delete_", source)
            self.assertNotIn("confirm_action(", source)

    def test_secondary_hubs_are_reduced_to_essential_actions(self):
        self.assertIn("Dados do MEI", self.account)
        self.assertIn("Backup e exportação", self.account)
        self.assertIn("Abrir automações", self.productivity)
        self.assertIn("Abrir alertas", self.productivity)
        self.assertNotIn("navigation_card(", self.account)
        self.assertNotIn("navigation_card(", self.productivity)


if __name__ == "__main__":
    unittest.main()
