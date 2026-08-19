from __future__ import annotations

import unittest
from unittest.mock import patch

from assistant_workspace import (
    DEFAULT_DAILY_REQUEST_LIMIT,
    DEFAULT_UI_MODEL,
    _daily_request_limit,
    _diagnose_ai,
)


class AIUsageControlTests(unittest.TestCase):
    @patch("assistant_workspace._secret", return_value="")
    def test_daily_limit_uses_safe_default(self, _secret):
        self.assertEqual(_daily_request_limit(), DEFAULT_DAILY_REQUEST_LIMIT)

    @patch("assistant_workspace._secret", return_value="12")
    def test_daily_limit_accepts_configured_value(self, _secret):
        self.assertEqual(_daily_request_limit(), 12)

    @patch("assistant_workspace._secret", return_value="invalid")
    def test_daily_limit_falls_back_for_invalid_value(self, _secret):
        self.assertEqual(_daily_request_limit(), DEFAULT_DAILY_REQUEST_LIMIT)

    @patch("assistant_workspace._secret", return_value="0")
    def test_daily_limit_never_allows_zero(self, _secret):
        self.assertEqual(_daily_request_limit(), 1)

    def test_diagnostic_reports_missing_key_without_external_call(self):
        ok, message = _diagnose_ai("", DEFAULT_UI_MODEL)
        self.assertFalse(ok)
        self.assertIn("OPENAI_API_KEY", message)


if __name__ == "__main__":
    unittest.main()
