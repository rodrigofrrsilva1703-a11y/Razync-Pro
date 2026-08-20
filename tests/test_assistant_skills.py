from __future__ import annotations

import unittest

from assistant_skills import build_skill_directive, select_response_skill
from ai_assistant import build_ai_prompt


class AssistantSkillTests(unittest.TestCase):
    def test_financial_question_selects_financial_skill(self):
        skill = select_response_skill("Por que minhas despesas aumentaram este mês?")
        self.assertEqual(skill.key, "financial")

    def test_fiscal_question_selects_fiscal_skill(self):
        skill = select_response_skill("Tenho DAS em atraso?")
        self.assertEqual(skill.key, "fiscal")

    def test_planning_question_selects_planner_skill(self):
        skill = select_response_skill("O que devo organizar primeiro?")
        self.assertEqual(skill.key, "planner")

    def test_prompt_contains_selected_skill_without_extra_provider_call(self):
        label, directive = build_skill_directive("Como está meu resultado financeiro?")
        prompt = build_ai_prompt(
            "Como está meu resultado financeiro?",
            context={"financial": {"result": 1200.0}},
            conversation=[],
        )
        self.assertIn(label, prompt)
        self.assertIn(directive, prompt)
        self.assertIn("1200.0", prompt)


if __name__ == "__main__":
    unittest.main()
