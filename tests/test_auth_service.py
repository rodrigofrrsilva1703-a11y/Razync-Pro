import unittest
from unittest.mock import patch

import auth_service


class AuthServiceConfigurationTests(unittest.TestCase):
    def test_publishable_defaults_activate_auth_without_secret_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(auth_service.is_supabase_auth_configured())
            client = auth_service._client()
            self.assertIsNotNone(client)

    def test_secret_values_override_publishable_defaults(self):
        with patch.dict(
            "os.environ",
            {
                "SUPABASE_URL": "https://example.supabase.co",
                "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
            },
            clear=True,
        ):
            self.assertTrue(auth_service.is_supabase_auth_configured())


class AuthServiceSessionTests(unittest.TestCase):
    def test_restore_session_rotates_tokens_and_returns_verified_identity(self):
        from types import SimpleNamespace

        user = SimpleNamespace(
            id="auth-user-id",
            email="dev@example.com",
            user_metadata={"name": "Dev"},
        )
        session = SimpleNamespace(
            access_token="new-access",
            refresh_token="new-refresh",
        )
        client = SimpleNamespace(
            auth=SimpleNamespace(
                refresh_session=lambda token: SimpleNamespace(user=user, session=session)
            )
        )

        with patch("auth_service._client", return_value=client):
            identity = auth_service.restore_session("old-refresh")

        self.assertEqual(identity["auth_user_id"], "auth-user-id")
        self.assertEqual(identity["access_token"], "new-access")
        self.assertEqual(identity["refresh_token"], "new-refresh")


if __name__ == "__main__":
    unittest.main()
