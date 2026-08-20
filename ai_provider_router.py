from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderChainError(RuntimeError):
    """Raised after every configured external AI provider has failed."""

    attempted_providers: tuple[str, ...]

    def __str__(self) -> str:
        providers = " e ".join(self.attempted_providers)
        return f"Nenhum provedor respondeu: {providers}." if providers else "Nenhum provedor de IA foi configurado."


def run_provider_chain(
    attempts: Iterable[tuple[str, Callable[[], str]]],
) -> tuple[str, str, tuple[str, ...]]:
    """Try providers in order and return answer, provider used and prior failures."""
    failed: list[str] = []
    for provider_name, request in attempts:
        name = str(provider_name or "Provedor").strip() or "Provedor"
        try:
            answer = str(request() or "").strip()
        except Exception:
            failed.append(name)
            continue
        if answer:
            return answer, name, tuple(failed)
        failed.append(name)
    raise ProviderChainError(tuple(failed))
