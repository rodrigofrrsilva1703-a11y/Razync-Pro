from __future__ import annotations

import unittest

from assistant_personality import select_conversation_style
from assistant_skills import build_skill_directive


class AssistantPersonalityTests(unittest.TestCase):
    def test_supportive_style_for_user_who_needs_help(self):
        style = select_conversation_style("Não entendi isso, me ajuda por favor")
        self.assertEqual(style.key, "supportive")
        self.assertIn("acolhedor", style.directive.lower())

    def test_analytical_style_for_business_analysis(self):
        style = select_conversation_style("Analise minha margem e compare com o mês passado")
        self.assertEqual(style.key, "analytical")

    def test_teaching_style_for_explanation(self):
        style = select_conversation_style("Me explica o que é fluxo de caixa")
        self.assertEqual(style.key, "teaching")

    def test_skill_directive_combines_expertise_and_humanized_behavior(self):
        label, directive = build_skill_directive("Estou preocupado com minhas despesas, me ajuda")
        self.assertIn("Analista financeiro", label)
        self.assertIn("Acolhedor e resolutivo", label)
        self.assertIn("sem fingir ser uma pessoa real", directive)
        self.assertIn("Transforme números em significado", directive)
        self.assertIn("memória da conversa", directive)
        self.assertIn("só faça uma pergunta de esclarecimento", directive)

    def test_neutral_style_stays_professional_without_fake_emotion(self):
        style = select_conversation_style("Mostre as ferramentas disponíveis")
        self.assertEqual(style.key, "neutral")
        self.assertIn("profissional", style.directive.lower())


if __name__ == "__main__":
    unittest.main()
