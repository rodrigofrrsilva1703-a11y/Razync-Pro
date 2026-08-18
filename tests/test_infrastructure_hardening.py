from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

import monitoring
from account_deletion import AccountDeletionError, delete_account
from scripts.backup_production import derive_key


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b'{"deleted": true}'


class InfrastructureHardeningTests(unittest.TestCase):
    def test_account_deletion_requires_session(self):
        with self.assertRaises(AccountDeletionError):
            delete_account("")

    @patch("account_deletion.urlopen", return_value=_Response())
    def test_account_deletion_calls_protected_edge_function(self, mocked_urlopen):
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
        }, clear=False):
            delete_account("user-jwt")
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.supabase.co/functions/v1/delete-account")
        self.assertEqual(request.headers["Authorization"], "Bearer user-jwt")
        self.assertEqual(request.headers["Apikey"], "sb_publishable_test")

    def test_backup_key_derivation_is_stable_and_salted(self):
        salt_a = b"a" * 16
        salt_b = b"b" * 16
        key_a1 = derive_key("strong-passphrase", salt_a)
        key_a2 = derive_key("strong-passphrase", salt_a)
        key_b = derive_key("strong-passphrase", salt_b)
        self.assertEqual(len(key_a1), 32)
        self.assertEqual(key_a1, key_a2)
        self.assertNotEqual(key_a1, key_b)

    def test_sentry_scrubber_removes_sensitive_context(self):
        event = {
            "request": {"data": "secret"},
            "user": {"email": "person@example.com"},
            "breadcrumbs": [{"message": "private"}],
            "extra": {"document": "private"},
            "contexts": {"runtime": {"name": "python"}, "custom": {"cpf": "x"}},
        }
        cleaned = monitoring._scrub_sentry_event(event, {})
        self.assertNotIn("request", cleaned)
        self.assertNotIn("user", cleaned)
        self.assertNotIn("breadcrumbs", cleaned)
        self.assertNotIn("extra", cleaned)
        self.assertIn("runtime", cleaned["contexts"])
        self.assertNotIn("custom", cleaned["contexts"])


if __name__ == "__main__":
    unittest.main()
