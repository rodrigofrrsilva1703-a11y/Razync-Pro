from pathlib import Path
import unittest


class DasOfficialFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Path("app.py").read_text(encoding="utf-8")
        cls.customer_experience = Path("customer_experience.py").read_text(encoding="utf-8")

    def test_uses_only_official_pgmei_destination(self):
        self.assertIn(
            "https://www8.receita.fazenda.gov.br/simplesnacional/aplicacoes/atspo/pgmei.app/identificacao",
            self.customer_experience,
        )
        self.assertIn('OFFICIAL_SERVICES["das"]["url"]', self.app)
        self.assertIn("Gerar DAS no site oficial", self.app)
        self.assertIn("nunca pede nem armazena sua senha gov.br", self.app)

    def test_can_store_the_official_guide_with_the_competence(self):
        self.assertIn('key="das_guide_upload"', self.app)
        self.assertIn('save_uploaded_document(user,guide,"DAS",competence)', self.app)
        self.assertIn('upsert_das(uid,competence,due,amount,status,payment_date,notes)', self.app)


if __name__ == "__main__":
    unittest.main()
