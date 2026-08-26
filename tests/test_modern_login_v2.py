from pathlib import Path
import unittest


class ModernLoginV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("workspace_style.py").read_text(encoding="utf-8")

    def test_marketing_hero_is_hidden(self):
        for token in (
            ".rz-login-kicker",
            ".rz-login-shell h1",
            ".rz-login-lead",
            ".rz-login-benefits",
            ".rz-login-proof",
        ):
            self.assertIn(token, self.source)
        self.assertIn("display: none !important", self.source)

    def test_auth_card_is_prominent_and_centered(self):
        self.assertIn("max-width: 440px !important", self.source)
        self.assertIn("border-radius: 22px !important", self.source)
        self.assertIn("box-shadow: 0 28px 80px", self.source)

    def test_demo_is_moved_to_secondary_footer_action(self):
        self.assertIn("position: fixed !important", self.source)
        self.assertIn("bottom: 1rem !important", self.source)
        self.assertIn("border-radius: 999px !important", self.source)

    def test_mobile_login_keeps_compact_spacing(self):
        self.assertIn("@media (max-width: 480px)", self.source)
        self.assertIn("padding-left: .55rem !important", self.source)


if __name__ == "__main__":
    unittest.main()
