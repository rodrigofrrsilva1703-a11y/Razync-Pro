import unittest
from pathlib import Path


class StreamlitChromeTests(unittest.TestCase):
    def test_native_chrome_is_minimal_and_errors_are_private(self):
        config = Path(".streamlit/config.toml").read_text(encoding="utf-8")
        self.assertIn('toolbarMode = "minimal"', config)
        self.assertIn("showErrorDetails = false", config)
        self.assertIn("showErrorLinks = false", config)

    def test_design_system_hides_nonessential_streamlit_elements(self):
        design = Path("ui_system.py").read_text(encoding="utf-8")
        self.assertIn("#MainMenu, footer", design)
        self.assertIn('[data-testid="stDecoration"]', design)
        self.assertIn('[data-testid="stStatusWidget"]', design)
        self.assertIn('button:not([data-testid="stExpandSidebarButton"])', design)


if __name__ == "__main__":
    unittest.main()

