from __future__ import annotations

import unittest

from assistant_personality import select_conversation_style
from assistant_response_policy import humanize_local_response, normalize_response, response_policy_directive


class AssistantResponsePolicyTests(unittest.TestCase):
    def test_followup_style_uses_recent_context(self):
        conversation = [
            {"role": "user", "content": "Estou preocupado com minhas despesas"},
            {"role": "assistant", "content": "Vamos revisar as categorias."},
        ]
        style = select_conversation_style("E agora?", conversation)
        self.assertEqual(style.key, "continuation")

    def test_recent_supportive_context_can_carry_tone(self):
        conversation = [{"role": "user", "content": "Não entendi meu fluxo de caixa, me ajuda"}]
        style = select_conversation_style("Pode continuar", conversation)
        self.assertEqual(style.key, "continuation")

    def test_local_humanization_preserves_money_and_percentages(self):
        original = "O resultado é R$ 1.250,50 e a margem é 18,4%."
        answer = humanize_local_response(original, question="Estou preocupado, me ajuda", source="product")
        self.assertIn("R$ 1.250,50", answer)
        self.assertIn("18,4%", answer)
        self.assertTrue(answer.startswith("Entendi. "))

    def test_continuation_adds_only_non_factual_framing(self):
        original = "A receita registrada é R$ 900,00."
        answer = humanize_local_response(original, question="E agora?", source="product")
        self.assertEqual(answer, "Seguindo o que estávamos vendo: " + original)

    def test_action_source_is_not_reframed_as_completed(self):
        original = "Pronto — preparei a ação. Confira o resumo e confirme para salvar."
        answer = humanize_local_response(original, question="E agora?", source="action")
        self.assertEqual(answer, original)
        self.assertNotIn("salvei", answer.lower())

    def test_normalization_does_not_change_numbers(self):
        original = "Receita R$ 2.000,00.\n\n\nDespesa R$ 750,00."
        answer = normalize_response(original)
        self.assertIn("R$ 2.000,00", answer)
        self.assertIn("R$ 750,00", answer)

    def test_common_policy_blocks_fake_execution_and_canned_tone(self):
        directive = response_policy_directive().lower()
        self.assertIn("preserve exatamente os números", directive)
        self.assertIn("não prometa que uma ação foi executada", directive)
        self.assertIn("não use elogios automáticos", directive)


if __name__ == "__main__":
    unittest.main()
