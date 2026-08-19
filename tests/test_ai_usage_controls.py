from __future__ import annotations

from datetime import date, datetime, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import text

from assistant_workspace import (
    DEFAULT_DAILY_REQUEST_LIMIT,
    DEFAULT_UI_MODEL,
    _daily_request_limit,
    _diagnose_ai,
)
from ai_usage_store import get_ai_usage, release_ai_request, reserve_ai_request, utc_usage_date
from database import DATABASE_URL, engine


class AIUsageControlTests(unittest.TestCase):
    def test_default_daily_limit_is_twenty(self):
        self.assertEqual(DEFAULT_DAILY_REQUEST_LIMIT, 20)

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

    def test_usage_day_is_utc(self):
        self.assertEqual(utc_usage_date(), datetime.now(timezone.utc).date())

    def test_diagnostic_reports_missing_key_without_external_call(self):
        ok, message = _diagnose_ai("", DEFAULT_UI_MODEL)
        self.assertFalse(ok)
        self.assertIn("OPENAI_API_KEY", message)

    @unittest.skipUnless(str(DATABASE_URL).startswith("sqlite"), "SQLite contract test")
    def test_twenty_reservations_allowed_and_twenty_first_blocked(self):
        uid = 987654321
        day = date(2099, 1, 1)
        get_ai_usage(uid, day)  # creates the local contract table when needed
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM ai_daily_usage WHERE user_id = :uid"), {"uid": uid})
        try:
            for expected in range(1, 21):
                allowed, count = reserve_ai_request(uid, 20, day)
                self.assertTrue(allowed)
                self.assertEqual(count, expected)
            allowed, count = reserve_ai_request(uid, 20, day)
            self.assertFalse(allowed)
            self.assertEqual(count, 20)
            self.assertEqual(get_ai_usage(uid, day), 20)
        finally:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM ai_daily_usage WHERE user_id = :uid"), {"uid": uid})

    @unittest.skipUnless(str(DATABASE_URL).startswith("sqlite"), "SQLite contract test")
    def test_failed_provider_reservation_can_be_refunded(self):
        uid = 987654322
        day = date(2099, 1, 2)
        get_ai_usage(uid, day)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM ai_daily_usage WHERE user_id = :uid"), {"uid": uid})
        try:
            allowed, count = reserve_ai_request(uid, 20, day)
            self.assertTrue(allowed)
            self.assertEqual(count, 1)
            self.assertEqual(release_ai_request(uid, day), 0)
            self.assertEqual(get_ai_usage(uid, day), 0)
        finally:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM ai_daily_usage WHERE user_id = :uid"), {"uid": uid})


if __name__ == "__main__":
    unittest.main()
