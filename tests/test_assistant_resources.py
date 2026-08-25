from __future__ import annotations

import unittest

from assistant_resources import build_product_context, should_prepare_resources, suggest_route
from assistant_skills import select_response_skill


class AssistantResourceTests(unittest.TestCase):
    def test_unknown_product_question_uses_general_copilot(self):
        skill = select_response_skill("Quero entender melhor o que consigo fazer aqui")
        self.assertEqual(skill.key, "product")

    def test_document_request_uses_document_skill(self):
        skill = select_response_skill("Quero baixar os documentos que anexei")
        self.assertEqual(skill.key, "documents")

    def test_route_understands_registration_request(self):
        route, label = suggest_route("Onde cadastro uma nova receita?")
        self.assertEqual(route, "Movimentações")
        self.assertIn("Movimentações", label)

    def test_product_context_exposes_capabilities_without_filenames(self):
        context = build_product_context(
            [
                {"filename": "segredo.pdf", "category": "DAS"},
                {"filename": "cliente-confidencial.pdf", "category": "Nota Fiscal"},
            ],
            current_page="Dashboard",
        )
        rendered = str(context)
        self.assertEqual(context["documents_available_count"], 2)
        self.assertIn("Documentos", context["available_areas"])
        self.assertNotIn("segredo.pdf", rendered)
        self.assertNotIn("cliente-confidencial.pdf", rendered)

    def test_resource_work_is_skipped_for_a_plain_open_question(self):
        self.assertFalse(should_prepare_resources("Como está meu negócio hoje?"))

    def test_resource_work_is_enabled_for_reports_and_navigation(self):
        self.assertTrue(should_prepare_resources("Gere um relatório financeiro em PDF"))
        self.assertTrue(should_prepare_resources("Onde cadastro uma receita?"))


if __name__ == "__main__":
    unittest.main()
