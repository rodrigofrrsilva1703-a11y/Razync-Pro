from pathlib import Path
import unittest


class LoginUiRegressionTests(unittest.TestCase):
    def test_app_has_no_development_login_bypass(self):
        root = Path(__file__).resolve().parents[1]
        app_source = (root / "app.py").read_text(encoding="utf-8")
        sidebar_source = (root / "sidebar_workspace.py").read_text(encoding="utf-8")
        self.assertNotIn('email = "dev@local"', app_source)
        self.assertNotIn('password = "dev"', app_source)
        self.assertIn('st.form("login_form")', app_source)
        self.assertIn('st.form("signup_form")', app_source)
        self.assertIn('st.form("password_recovery_form")', app_source)
        self.assertIn("supabase_sign_in", app_source)
        self.assertIn("github_sign_in", app_source)
        self.assertIn("resolve_trusted_developer_user", app_source)
        self.assertIn("Entrar como desenvolvedor com GitHub", app_source)
        callback = app_source.index("identity = github_sign_in")
        session_saved = app_source.index(
            'st.session_state["user"] = user', callback
        )
        callback_cleared = app_source.index("st.query_params.clear()", callback)
        self.assertLess(session_saved, callback_cleared)
        self.assertIn('st.button("Sair"', sidebar_source)
        workflows = root / ".github" / "workflows"
        self.assertEqual(
            {path.name for path in workflows.glob("*.yml")},
            {"ci.yml", "tests.yml", "production-backup.yml"},
        )
        backup_source = (workflows / "production-backup.yml").read_text(encoding="utf-8")
        self.assertIn("RAZYNC_BACKUP_DATABASE_URL", backup_source)
        self.assertIn("RAZYNC_BACKUP_SUPABASE_SECRET_KEY", backup_source)
        self.assertNotIn("service_role", backup_source.lower())
        self.assertFalse((root / "preview_access.py").exists())
        self.assertFalse((root / "preview_app.py").exists())


if __name__ == "__main__":
    unittest.main()
