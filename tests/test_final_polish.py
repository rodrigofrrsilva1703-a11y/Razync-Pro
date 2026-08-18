from pathlib import Path
import unittest


class FinalPolishTests(unittest.TestCase):
    def test_sidebar_is_modularized(self):
        self.assertTrue(Path("sidebar_workspace.py").exists())
        app = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("from sidebar_workspace import render_sidebar", app)
        self.assertIn("render_sidebar(", app)
        self.assertNotIn("with st.sidebar:\n", app)

    def test_snapshot_version_check_is_local(self):
        db = Path("database.py").read_text(encoding="utf-8")
        self.assertIn("_USER_VERSION", db)
        self.assertIn("def data_version(user_id: int) -> int:", db)
        self.assertIn("return _USER_VERSION.get(int(user_id), 0)", db)

    def test_performance_snapshot_contract_remains(self):
        app = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("load_user_snapshot(uid)", app)
        self.assertIn("_snapshot_key", app)
        self.assertIn("data_version(uid)", app)


if __name__ == "__main__":
    unittest.main()
