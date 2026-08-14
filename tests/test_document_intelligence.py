import unittest
from unittest.mock import patch

from document_intelligence import analyze_document


class DocumentIntelligenceTests(unittest.TestCase):
    @patch("document_intelligence._extract_pdf_text")
    def test_extracts_confirmable_pdf_suggestions(self, extract):
        extract.return_value = """
        NOTA FISCAL DE SERVIÇOS ELETRÔNICA
        Número: 20260042
        Competência: 07/2026
        Valor total R$ 1.234,56
        """
        result = analyze_document(b"%PDF", "application/pdf", "nota.pdf")
        self.assertEqual(result["category"], "Nota Fiscal")
        self.assertEqual(result["reference_month"], "2026-07")
        self.assertEqual(result["value"], 1234.56)
        self.assertEqual(result["document_number"], "20260042")
        self.assertTrue(result["has_searchable_text"])
        self.assertEqual(result["confidence"], "Alta")

    def test_image_uses_filename_and_explains_manual_review(self):
        result = analyze_document(b"image", "image/png", "comprovante_pix_2026-08.png")
        self.assertEqual(result["category"], "Comprovante")
        self.assertEqual(result["reference_month"], "2026-08")
        self.assertFalse(result["has_searchable_text"])
        self.assertIn("não possuem leitura automática", result["warning"])


if __name__ == "__main__":
    unittest.main()
