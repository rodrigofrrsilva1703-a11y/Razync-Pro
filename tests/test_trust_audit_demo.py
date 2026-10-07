from pathlib import Path
import unittest


class TrustAuditDirectAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Path("app.py").read_text(encoding="utf-8")
        cls.demo = Path("demo_mode.py").read_text(encoding="utf-8")
        cls.migration = Path(
            "supabase/migrations/20260814163000_audit_history.sql"
        ).read_text(encoding="utf-8").lower()

    def test_direct_access_is_explicit_and_does_not_fake_authentication(self):
        self.assertIn("resolve_public_workspace_user", self.app)
        self.assertIn('st.session_state["auth_provider"] = "public"', self.app)
        self.assertNotIn('st.form("login_form")', self.app)
        self.assertNotIn('st.form("signup_form")', self.app)

    def test_demo_module_remains_isolated_even_while_not_exposed(self):
        self.assertNotIn("render_demo()", self.app)
        self.assertNotIn("from database", self.demo)
        self.assertIn("dados fictícios", self.demo.lower())

    def test_audit_table_has_rls_owner_policy_and_safe_payload(self):
        self.assertIn("enable row level security", self.migration)
        self.assertIn("audit_logs_owner_select", self.migration)
        self.assertIn("auth.uid()", self.migration)
        self.assertIn("- 'password_hash' - 'content'", self.migration)
        self.assertIn("ix_audit_logs_user_created", self.migration)
        self.assertIn("revoke all on function", self.migration)


if __name__ == "__main__":
    unittest.main()
