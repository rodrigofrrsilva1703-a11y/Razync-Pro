import unittest

from login_security import LoginAttemptGuard


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class LoginAttemptGuardTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.guard = LoginAttemptGuard(
            max_failures=3,
            lock_seconds=120,
            clock=self.clock,
        )

    def test_locks_after_maximum_failures(self):
        self.assertEqual(self.guard.record_failure("USER@example.com"), 0)
        self.assertEqual(self.guard.record_failure("user@example.com"), 0)
        self.assertEqual(self.guard.record_failure(" user@example.com "), 120)
        self.assertEqual(self.guard.retry_after("user@example.com"), 120)

    def test_unlocks_after_timeout(self):
        for _ in range(3):
            self.guard.record_failure("user@example.com")

        self.clock.advance(119)
        self.assertEqual(self.guard.retry_after("user@example.com"), 1)
        self.clock.advance(1)
        self.assertEqual(self.guard.retry_after("user@example.com"), 0)

    def test_success_clears_failures(self):
        self.guard.record_failure("user@example.com")
        self.guard.record_failure("user@example.com")
        self.guard.record_success("user@example.com")

        self.assertEqual(self.guard.record_failure("user@example.com"), 0)
        self.assertEqual(self.guard.retry_after("user@example.com"), 0)

    def test_accounts_are_isolated(self):
        for _ in range(3):
            self.guard.record_failure("blocked@example.com")

        self.assertEqual(self.guard.retry_after("blocked@example.com"), 120)
        self.assertEqual(self.guard.retry_after("other@example.com"), 0)


if __name__ == "__main__":
    unittest.main()
