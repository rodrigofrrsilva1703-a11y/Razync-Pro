from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from threading import Lock
from time import monotonic


DEFAULT_PROVIDER_COOLDOWN_SECONDS = 120.0
_provider_lock = Lock()
_provider_cooldowns: dict[str, float] = {}
_preferred_provider = ""


@dataclass(frozen=True)
class ProviderChainError(RuntimeError):
    """Raised after every configured external AI provider has failed."""

    attempted_providers: tuple[str, ...]

    def __str__(self) -> str:
        providers = " e ".join(self.attempted_providers)
        return f"Nenhum provedor respondeu: {providers}." if providers else "Nenhum provedor de IA foi configurado."


def run_provider_chain(
    attempts: Iterable[tuple[str, Callable[[], str]]],
    *,
    cooldown_seconds: float = DEFAULT_PROVIDER_COOLDOWN_SECONDS,
) -> tuple[str, str, tuple[str, ...]]:
    """Try healthy providers, remembering the fastest working fallback.

    A provider that just failed is temporarily skipped. This avoids making every
    user wait for the same timeout while an API is unavailable or misconfigured.
    """
    global _preferred_provider
    configured = list(attempts)
    with _provider_lock:
        preferred = _preferred_provider
    if preferred:
        configured.sort(key=lambda item: 0 if str(item[0]).strip() == preferred else 1)

    failed: list[str] = []
    for provider_name, request in configured:
        name = str(provider_name or "Provedor").strip() or "Provedor"
        now = monotonic()
        with _provider_lock:
            unavailable_until = _provider_cooldowns.get(name, 0.0)
        if unavailable_until > now:
            failed.append(name)
            continue
        try:
            answer = str(request() or "").strip()
        except Exception:
            failed.append(name)
            with _provider_lock:
                _provider_cooldowns[name] = monotonic() + max(0.0, float(cooldown_seconds))
            continue
        if answer:
            with _provider_lock:
                _provider_cooldowns.pop(name, None)
                _preferred_provider = name
            return answer, name, tuple(failed)
        failed.append(name)
        with _provider_lock:
            _provider_cooldowns[name] = monotonic() + max(0.0, float(cooldown_seconds))
    raise ProviderChainError(tuple(failed))


def reset_provider_health() -> None:
    """Clear in-process health memory (used by diagnostics and tests)."""
    global _preferred_provider
    with _provider_lock:
        _provider_cooldowns.clear()
        _preferred_provider = ""
