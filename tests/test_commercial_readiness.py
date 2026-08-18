from io import BytesIO
from pathlib import Path
import unittest

from reportlab.pdfgen import canvas

from commercial_readiness import PLAN_CATALOG, data_rights_summary, integration_maturity, production_checklist
from fiscal_automation import analyze_das_guide
from validators import cpf_or_cnpj_status, valid_cnpj, valid_competence, valid_cpf


class CommercialReadinessTests(unittest.TestCase):
    def test_document_validators(self):
        self.assertTrue(valid_cpf("529.982.247-25"))
        self.assertFalse(valid_cpf("111.111.111-11"))
        self.assertTrue(valid_cnpj("04.252.011/0001-10"))
        self.assertFalse(valid_cnpj("11.111.111/1111-11"))
        self.assertTrue(valid_competence("2026-08"))
        self.assertFalse(valid_competence("08/2026"))
        self.assertEqual(cpf_or_cnpj_status("")[0], True)

    def test_das_pdf_is_read_without_external_service(self):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(50, 780, "Documento de Arrecadacao do Simples Nacional - DAS MEI")
        pdf.drawString(50, 760, "Competencia: 08/2026")
        pdf.drawString(50, 740, "Valor: R$ 82,90")
        pdf.save()
        result = analyze_das_guide(buffer.getvalue(), "das-2026-08.pdf")
        self.assertTrue(result["recognized_as_das"])
        self.assertEqual(result["competence"], "2026-08")
        self.assertAlmostEqual(result["amount"], 82.90, places=2)

    def test_commercial_contracts_are_explicit(self):
        self.assertIn("Essencial", PLAN_CATALOG)
        self.assertIn("Pro", PLAN_CATALOG)
        self.assertEqual(integration_maturity({"name": "NFS-e Nacional", "ready": True}), "Assistido")
        checklist = production_checklist(
            persistent_db=True,
            auth_ready=True,
            storage_ready=True,
            session_secret=True,
        )
        self.assertTrue(checklist[0]["ok"])
        self.assertTrue(any(not item["ok"] for item in checklist if item["item"] in {"Backup e restauração", "Monitoramento externo"}))
        rights = {item["title"]: item["status"] for item in data_rights_summary()}
        self.assertEqual(rights["Exportar meus dados"], "Disponível")
        self.assertEqual(rights["Excluir minha conta"], "Processo assistido")

    def test_new_hubs_remain_in_navigation_contract(self):
        product_core = Path("product_core.py").read_text(encoding="utf-8")
        navigation = Path("navigation_config.py").read_text(encoding="utf-8")
        self.assertIn('"Produtividade"', product_core)
        self.assertIn('"Conta e Sistema"', product_core)
        self.assertIn('"Produtividade": "Produtividade"', navigation)
        self.assertIn('"Conta e Sistema": "Conta e sistema"', navigation)


if __name__ == "__main__":
    unittest.main()
