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


if __name__ == "__main__":
    unittest.main()
