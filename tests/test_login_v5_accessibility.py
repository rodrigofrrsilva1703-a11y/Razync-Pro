from pathlib import Path
import unittest


class LoginV5AccessibilityTests(unittest.TestCase):
    """Protege acessibilidade e interações não obrigatórias do login V5."""

    @classmethod
    def setUpClass(cls):
        cls.source = Path("workspace_style.py").read_text(encoding="utf-8")

    def test_reduced_motion_is_respected(self):
        self.assertIn("prefers-reduced-motion: reduce", self.source)
        self.assertIn("animation: none !important", self.source)
        self.assertIn("transition: none !important", self.source)

    def test_interactions_are_not_required_for_core_login(self):
        self.assertIn("[data-baseweb=\"input\"]:focus-within", self.source)
        self.assertIn("[data-testid=\"stFormSubmitButton\"] button:hover", self.source)
        self.assertNotIn("pointer-events: none !important;\n            opacity: 0", self.source)


if __name__ == "__main__":
    unittest.main()
