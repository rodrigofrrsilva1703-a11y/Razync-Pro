from pathlib import Path
import unittest


class TrustAuditDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Path("app.py").read_text(encoding="utf-8")
        cls.migration = Path("supabase/migrations/20260814163000_audit_history.sql").read_text(encoding="utf-8").lower()

    def test_signup_requires_legal_consent(self):
        self.assertIn("signup_legal_consent", self.app)
        self.assertIn("Aceite os Termos de Uso", self.app)
        self.assertIn("PRIVACY_NOTICE", self.app)

    def test_demo_is_explicitly_isolated(self):
        self.assertIn("Explorar demonstração sem criar conta", self.app)
        self.assertIn("render_demo()", self.app)
        demo = Path("demo_mode.py").read_text(encoding="utf-8")
        self.assertNotIn("from database", demo)
        self.assertIn("Dados fictícios", demo)

    def test_audit_table_has_rls_owner_policy_and_safe_payload(self):
        self.assertIn("enable row level security", self.migration)
        self.assertIn("audit_logs_owner_select", self.migration)
        self.assertIn("auth.uid()", self.migration)
        self.assertIn("- 'password_hash' - 'content'", self.migration)
        self.assertIn("ix_audit_logs_user_created", self.migration)
        self.assertIn("revoke all on function", self.migration)


if __name__ == "__main__":
    unittest.main()
