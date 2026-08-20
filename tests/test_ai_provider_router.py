from __future__ import annotations

import unittest

from ai_provider_router import ProviderChainError, run_provider_chain


class ProviderRouterTests(unittest.TestCase):
    def test_returns_primary_provider_without_calling_fallback(self):
        calls: list[str] = []

        def primary() -> str:
            calls.append("Gemini")
            return "Resposta principal"

        def fallback() -> str:
            calls.append("OpenAI")
            return "Resposta reserva"

        answer, provider, failed = run_provider_chain([("Gemini", primary), ("OpenAI", fallback)])

        self.assertEqual(answer, "Resposta principal")
        self.assertEqual(provider, "Gemini")
        self.assertEqual(failed, ())
        self.assertEqual(calls, ["Gemini"])

    def test_uses_fallback_when_primary_fails(self):
        def primary() -> str:
            raise RuntimeError("indisponível")

        answer, provider, failed = run_provider_chain([
            ("Gemini", primary),
            ("OpenAI", lambda: "Resposta reserva"),
        ])

        self.assertEqual(answer, "Resposta reserva")
        self.assertEqual(provider, "OpenAI")
        self.assertEqual(failed, ("Gemini",))

    def test_empty_answer_is_treated_as_failure(self):
        answer, provider, failed = run_provider_chain([
            ("Gemini", lambda: "   "),
            ("OpenAI", lambda: "OK"),
        ])
        self.assertEqual((answer, provider, failed), ("OK", "OpenAI", ("Gemini",)))

    def test_raises_only_after_all_providers_fail(self):
        with self.assertRaises(ProviderChainError) as context:
            run_provider_chain([
                ("Gemini", lambda: (_ for _ in ()).throw(RuntimeError("falhou"))),
                ("OpenAI", lambda: ""),
            ])
        self.assertEqual(context.exception.attempted_providers, ("Gemini", "OpenAI"))


if __name__ == "__main__":
    unittest.main()
