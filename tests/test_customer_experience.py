from datetime import date, datetime
import unittest

from product_core import NAV_GROUPS
from customer_experience import (
    build_today_plan, das_journey, financial_story, integration_catalog,
    next_onboarding_step, security_checklist, transaction_restore_payload,
)


class CustomerExperienceTests(unittest.TestCase):
    def test_next_onboarding_step_routes_to_feature(self):
        progress = {"steps": [
            {"key": "identity", "done": True, "detail": "ok"},
            {"key": "financial", "done": False, "detail": "primeiro lançamento"},
        ]}
        step = next_onboarding_step(progress)
        self.assertEqual(step["page"], "Movimentações")

    def test_today_plan_prioritizes_urgent_notification(self):
        plan = build_today_plan(
            [{"priority": 3, "title": "Configurar", "detail": "Dados", "page": "Meu MEI"}],
            [{"level": "urgent", "title": "DAS atrasado", "detail": "Vencido", "page": "DAS"}],
            {"steps": []},
        )
        self.assertEqual(plan["items"][0]["page"], "DAS")
        self.assertEqual(plan["urgent"], 1)

    def test_financial_story_explains_negative_month(self):
        story = financial_story(1000, 1500, 1000, 81000)
        self.assertEqual(story[0]["tone"], "danger")
        self.assertIn("saídas", story[0]["title"].lower())

    def test_das_journey_tracks_document_and_payment(self):
        journey = das_journey(
            "2026-08",
            [{"id": 1, "competence": "2026-08", "status": "Pago"}],
            [{"category": "DAS", "reference_month": "2026-08"}],
        )
        self.assertEqual(journey["percent"], 100)

    def test_integrations_never_claim_direct_open_finance(self):
        catalog = integration_catalog({}, True)
        banking = next(item for item in catalog if item["name"] == "Banco e Open Finance")
        self.assertEqual(banking["status"], "Importação ativa")
        self.assertIn("consentimento", banking["detail"])

    def test_restore_payload_removes_database_fields(self):
        payload = transaction_restore_payload({
            "id": 9,
            "user_id": 4,
            "tx_date": datetime(2026, 8, 15, 12, 0),
            "tx_type": "Receita",
            "description": "Venda",
            "category": "Vendas",
            "value": "150.50",
            "created_at": datetime.now(),
        })
        self.assertNotIn("id", payload)
        self.assertNotIn("user_id", payload)
        self.assertEqual(payload["tx_date"], date(2026, 8, 15))
        self.assertEqual(payload["value"], 150.5)

    def test_navigation_exposes_integration_center(self):
        self.assertIn("Integrações", NAV_GROUPS["Configurações"])

    def test_security_checklist_keeps_manual_setting_visible(self):
        checks = security_checklist(
            auth_enabled=True,
            database_persistent=True,
            storage_enabled=True,
            leaked_password_protection=False,
        )
        pending = [item for item in checks if not item["done"]]
        self.assertEqual(pending[0]["title"], "Proteção contra senhas vazadas")


if __name__ == "__main__":
    unittest.main()
