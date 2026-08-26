from pathlib import Path
import unittest


class LoginVisualMarketingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_source = Path("ui_system.py").read_text(encoding="utf-8")
        cls.workspace_source = Path("workspace_style.py").read_text(encoding="utf-8")

    def test_base_login_structure_is_preserved(self):
        self.assertIn(".rz-login-benefits", self.base_source)
        self.assertIn(".rz-login-proof", self.base_source)

    def test_workspace_reactivates_marketing_with_controlled_layout(self):
        self.assertIn(".rz-login-benefits", self.workspace_source)
        self.assertIn("display: grid !important", self.workspace_source)
        self.assertIn("max-width: 820px !important", self.workspace_source)

    def test_authentication_remains_visually_compact(self):
        self.assertIn("max-width: 460px !important", self.workspace_source)
        self.assertIn("border-radius: 22px !important", self.workspace_source)

    def test_demo_action_is_secondary(self):
        self.assertIn("border-radius: 999px !important", self.workspace_source)
        self.assertIn("color: var(--rz-muted) !important", self.workspace_source)


if __name__ == "__main__":
    unittest.main()
