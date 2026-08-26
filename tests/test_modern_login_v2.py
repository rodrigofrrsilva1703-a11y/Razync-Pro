from pathlib import Path
import unittest


class ModernLoginV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("workspace_style.py").read_text(encoding="utf-8")

    def test_marketing_hero_is_visible_and_structured(self):
        for token in (
            ".rz-login-kicker",
            ".rz-login-shell h1",
            ".rz-login-lead",
            ".rz-login-benefits",
            ".rz-login-proof",
        ):
            self.assertIn(token, self.source)
        self.assertIn("display: grid !important", self.source)
        self.assertIn("grid-template-columns: repeat(3", self.source)

    def test_auth_card_remains_compact_and_centered(self):
        self.assertIn("max-width: 460px !important", self.source)
        self.assertIn("border-radius: 22px !important", self.source)
        self.assertIn("box-shadow: 0 28px 80px", self.source)

    def test_demo_remains_secondary_without_fixed_overlay(self):
        self.assertIn("border-radius: 999px !important", self.source)
        self.assertNotIn("bottom: 1rem !important", self.source)

    def test_mobile_stacks_marketing_benefits(self):
        self.assertIn("@media (max-width: 760px)", self.source)
        self.assertIn("grid-template-columns: 1fr !important", self.source)
        self.assertIn("@media (max-width: 480px)", self.source)


if __name__ == "__main__":
    unittest.main()
