from pathlib import Path
import unittest


class ModernLoginV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("workspace_style.py").read_text(encoding="utf-8")

    def test_split_screen_is_modern_and_has_no_diagonal_cut(self):
        self.assertIn("Login V5", self.source)
        self.assertIn("grid-template-columns: minmax(0, 1.12fr)", self.source)
        self.assertIn("linear-gradient(90deg, #061522 0 55%, #f9fcfe 55% 100%)", self.source)
        self.assertNotIn("linear-gradient(112deg", self.source)

    def test_marketing_panel_has_interactive_cards(self):
        for token in (
            ".rz-login-brand:hover .rz-login-mark",
            ".rz-login-benefits span:hover",
            ".rz-login-benefits span:hover::after",
            "transform: translateX(6px)",
        ):
            self.assertIn(token, self.source)

    def test_auth_card_has_modern_focus_and_hover_states(self):
        self.assertIn("max-width: 500px !important", self.source)
        self.assertIn("border-radius: 24px !important", self.source)
        self.assertIn("[data-baseweb=\"input\"]:focus-within", self.source)
        self.assertIn("[data-testid=\"stFormSubmitButton\"] button:hover", self.source)
        self.assertIn("linear-gradient(90deg, #0878ff 0%, #08b9ef 100%)", self.source)

    def test_demo_cta_remains_secondary_and_interactive(self):
        self.assertIn("Demonstração: CTA discreto e interativo", self.source)
        self.assertIn("[data-testid=\"stButton\"] button:hover", self.source)
        self.assertNotIn("position: fixed", self.source)

    def test_responsive_and_reduced_motion_are_supported(self):
        self.assertIn("@media (max-width: 980px)", self.source)
        self.assertIn("@media (max-width: 600px)", self.source)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.source)
        self.assertIn("grid-template-columns: 1fr !important", self.source)


if __name__ == "__main__":
    unittest.main()
