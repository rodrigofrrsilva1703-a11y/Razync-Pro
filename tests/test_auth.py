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


if __name__ == "__main__":
    unittest.main()
