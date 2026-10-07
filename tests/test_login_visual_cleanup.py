from pathlib import Path
import unittest


class DirectAccessVisualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_source = Path("ui_system.py").read_text(encoding="utf-8")
        cls.workspace_source = Path("workspace_style.py").read_text(encoding="utf-8")

    def test_obsolete_login_visual_layer_is_removed(self):
        self.assertNotIn(".rz-login-shell", self.base_source)
        self.assertNotIn(".rz-login-shell", self.workspace_source)
        self.assertNotIn(".rz-login-benefits", self.workspace_source)

    def test_workspace_has_consistent_saas_surface(self):
        self.assertIn("RAZYNC PRO · WORKSPACE V6", self.workspace_source)
        self.assertIn("max-width: 1280px !important", self.workspace_source)
        self.assertIn("var(--rz-surface)", self.workspace_source)
        self.assertIn("var(--rz-border)", self.workspace_source)

    def test_mobile_sidebar_does_not_cover_the_full_screen(self):
        self.assertIn("width: min(300px, 88vw) !important", self.workspace_source)
        self.assertIn("min-width: min(300px, 88vw) !important", self.workspace_source)

    def test_mobile_columns_stack_predictably(self):
        self.assertIn("@media (max-width: 520px)", self.workspace_source)
        self.assertIn("flex: 1 1 100% !important", self.workspace_source)
        self.assertIn("width: 100% !important", self.workspace_source)

    def test_reduced_motion_is_respected(self):
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.workspace_source)
        self.assertIn("animation: none !important", self.workspace_source)


if __name__ == "__main__":
    unittest.main()
