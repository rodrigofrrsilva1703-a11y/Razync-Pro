from pathlib import Path
import unittest


class LoginVisualCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("ui_system.py").read_text(encoding="utf-8")

    def test_marketing_chips_are_hidden_on_login(self):
        self.assertIn(".rz-login-benefits, .rz-login-proof { display:none!important; }", self.source)

    def test_auth_card_is_compact(self):
        self.assertIn("max-width:460px", self.source)
        self.assertIn("max-width:620px", self.source)

    def test_demo_action_is_visually_secondary(self):
        self.assertIn("[data-testid=\"stButton\"] button", self.source)
        self.assertIn("background:transparent!important", self.source)


if __name__ == "__main__":
    unittest.main()
