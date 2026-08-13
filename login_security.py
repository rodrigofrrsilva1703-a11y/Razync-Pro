from __future__ import annotations

from dataclasses import dataclass
import math
from threading import Lock
import time
from typing import Callable


@dataclass
class _AttemptState:
    failures: int = 0
    locked_until: float = 0.0


class LoginAttemptGuard:
    """Process-local login throttling without storing passwords or error details."""

    def __init__(
        self,
        max_failures: int = 5,
        lock_seconds: int = 300,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_failures < 1:
            raise ValueError("max_failures must be positive")
        if lock_seconds < 1:
            raise ValueError("lock_seconds must be positive")
        self.max_failures = max_failures
        self.lock_seconds = lock_seconds
        self._clock = clock
        self._states: dict[str, _AttemptState] = {}
        self._lock = Lock()

    @staticmethod
    def _key(email: str) -> str:
        return email.strip().lower()

    def retry_after(self, email: str) -> int:
        key = self._key(email)
        if not key:
            return 0

        now = self._clock()
        with self._lock:
            state = self._states.get(key)
            if state is None or state.locked_until <= now:
                if state is not None and state.locked_until:
                    self._states.pop(key, None)
                return 0
            return max(1, math.ceil(state.locked_until - now))

    def record_failure(self, email: str) -> int:
        key = self._key(email)
        if not key:
            return 0

        now = self._clock()
        with self._lock:
            state = self._states.setdefault(key, _AttemptState())
            if state.locked_until > now:
                return max(1, math.ceil(state.locked_until - now))

            state.failures += 1
            if state.failures >= self.max_failures:
                state.failures = 0
                state.locked_until = now + self.lock_seconds
                return self.lock_seconds
            return 0

    def record_success(self, email: str) -> None:
        key = self._key(email)
        if not key:
            return
        with self._lock:
            self._states.pop(key, None)


login_attempt_guard = LoginAttemptGuard()
