from pathlib import Path
import unittest


class ModernWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("workspace.css").read_text(encoding="utf-8")

    def test_page_hierarchy_is_editorial_and_responsive(self):
        self.assertIn("clamp(1.75rem,2.5vw,2.3rem)", self.source)
        self.assertIn("max-width: 690px", self.source)
        self.assertIn("max-width: 1360px !important", self.source)

    def test_kpi_strip_has_desktop_and_mobile_sizes(self):
        self.assertIn("min-height: 140px", self.source)
        self.assertIn("grid-template-columns: repeat(2,minmax(0,1fr))", self.source)

    def test_mobile_layout_stacks_columns(self):
        self.assertIn("@media (max-width: 820px)", self.source)
        self.assertIn("@media (max-width: 520px)", self.source)
        self.assertIn("flex: 1 1 100% !important", self.source)

    def test_floating_ai_remains_touch_friendly(self):
        self.assertIn(".st-key-floating_ai_launcher", self.source)
        self.assertIn("min-height: 46px", self.source)
        self.assertIn("border-radius: 999px", self.source)


if __name__ == "__main__":
    unittest.main()
