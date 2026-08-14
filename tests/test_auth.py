import importlib
import os
import tempfile
import unittest
from pathlib import Path


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = Path(tempfile.gettempdir()) / "razync_auth_test.db"
        if cls.db_path.exists():
            cls.db_path.unlink()
        os.environ["DATABASE_URL"] = f"sqlite:///{cls.db_path.as_posix()}"

        import database
        cls.database = importlib.reload(database)
        cls.database.init_db()

    @classmethod
    def tearDownClass(cls):
        cls.database.engine.dispose()
        if cls.db_path.exists():
            cls.db_path.unlink()

    def test_account_creation_and_authentication(self):
        created, message = self.database.create_user(
            "Usuário de Teste",
            "usuario@example.com",
            "senha-segura",
        )
        self.assertTrue(created, message)

        user = self.database.authenticate("USUARIO@example.com", "senha-segura")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "usuario@example.com")
        self.assertIsNone(
            self.database.authenticate("usuario@example.com", "senha-incorreta")
        )

    def test_links_confirmed_supabase_identity_to_existing_account(self):
        created, message = self.database.create_user(
            "Conta Legada", "legacy@example.com", "senha-segura"
        )
        self.assertTrue(created, message)

        linked = self.database.resolve_supabase_user(
            "12345678-1234-5678-1234-567812345678",
            "LEGACY@example.com",
            "Nome do Auth",
        )
        self.assertEqual(linked["email"], "legacy@example.com")
        self.assertEqual(
            linked["auth_user_id"],
            "12345678-1234-5678-1234-567812345678",
        )

        same = self.database.resolve_supabase_user(
            "12345678-1234-5678-1234-567812345678",
            "legacy@example.com",
        )
        self.assertEqual(same["id"], linked["id"])

    def test_rejects_invalid_registration_data(self):
        cases = [
            ("", "usuario@example.com", "senha-segura"),
            ("Usuário", "email-invalido", "senha-segura"),
            ("Usuário", "usuario@example.com", "curta"),
        ]
        for name, email, password in cases:
            with self.subTest(name=name, email=email):
                created, _ = self.database.create_user(name, email, password)
                self.assertFalse(created)


class LoginUiRegressionTests(unittest.TestCase):
    def test_app_has_no_development_login_bypass(self):
        app_source = (Path(__file__).resolve().parents[1] / "app.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('email = "dev@local"', app_source)
        self.assertNotIn('password = "dev"', app_source)
        self.assertIn('st.form("login_form")', app_source)
        self.assertIn('st.form("signup_form")', app_source)
        self.assertIn('st.form("password_recovery_form")', app_source)
        self.assertIn("supabase_sign_in", app_source)
        self.assertIn('st.button("Sair"', app_source)
        workflows = Path(__file__).resolve().parents[1] / ".github" / "workflows"
        self.assertEqual(
            {path.name for path in workflows.glob("*.yml")},
            {"ci.yml", "tests.yml"},
        )
        root = Path(__file__).resolve().parents[1]
        self.assertFalse((root / "preview_access.py").exists())
        self.assertFalse((root / "preview_app.py").exists())


if __name__ == "__main__":
    unittest.main()
