import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import auth_service


class AuthServiceConfigurationTests(unittest.TestCase):
    def test_publishable_defaults_activate_auth_without_secret_keys(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(auth_service.is_supabase_auth_configured())
            with patch("auth_service.create_client", return_value=object()) as factory:
                client = auth_service._client()
            self.assertIsNotNone(client)
            factory.assert_called_once_with(
                auth_service.DEFAULT_SUPABASE_URL,
                auth_service.DEFAULT_SUPABASE_PUBLISHABLE_KEY,
            )

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


class DeveloperGithubAuthTests(unittest.TestCase):
    secrets = {
        "GITHUB_CLIENT_ID": "client-id",
        "GITHUB_CLIENT_SECRET": "a-very-secret-value",
        "DEVELOPER_GITHUB_USER": "rodrigofrrsilva1703-a11y",
        "APP_URL": "https://app.example/",
    }

    def test_authorization_url_contains_signed_state_and_exact_callback(self):
        with patch.dict("os.environ", self.secrets, clear=True):
            url = auth_service.github_authorization_url()
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["client_id"], ["client-id"])
        self.assertEqual(query["redirect_uri"], ["https://app.example/"])
        self.assertTrue(query["state"][0].startswith("rzgh."))
        self.assertEqual(query["scope"], ["read:user user:email"])

    def test_only_configured_github_user_is_accepted(self):
        responses = [
            {"access_token": "token"},
            {
                "id": 123,
                "login": "rodrigofrrsilva1703-a11y",
                "name": "Rodrigo",
                "email": "dev@example.com",
            },
        ]
        with patch.dict("os.environ", self.secrets, clear=True):
            state = auth_service._github_state()
            with patch("auth_service._github_json_request", side_effect=responses):
                identity = auth_service.github_sign_in("valid-code", state)
        self.assertEqual(identity["github_login"], self.secrets["DEVELOPER_GITHUB_USER"])
        self.assertEqual(identity["provider"], "github")
        self.assertEqual(identity["email"], "dev@example.com")

    def test_different_github_user_is_rejected(self):
        responses = [
            {"access_token": "token"},
            {"id": 456, "login": "outra-conta", "email": "other@example.com"},
        ]
        with patch.dict("os.environ", self.secrets, clear=True):
            state = auth_service._github_state()
            with patch("auth_service._github_json_request", side_effect=responses):
                with self.assertRaisesRegex(auth_service.AuthServiceError, "não possui acesso"):
                    auth_service.github_sign_in("valid-code", state)

    def test_tampered_state_is_rejected_before_network_request(self):
        with patch.dict("os.environ", self.secrets, clear=True):
            with patch("auth_service._github_json_request") as request:
                with self.assertRaises(auth_service.AuthServiceError):
                    auth_service.github_sign_in("valid-code", "rzgh.1.nonce.invalid")
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
