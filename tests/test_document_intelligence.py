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

    @patch("document_intelligence._ocr_image_bytes")
    def test_image_uses_local_ocr(self, ocr):
        ocr.return_value = "Comprovante PIX realizado Valor R$ 199,90"
        result = analyze_document(b"image", "image/png", "comprovante_pix_2026-08.png")
        self.assertEqual(result["category"], "Comprovante")
        self.assertEqual(result["reference_month"], "2026-08")
        self.assertEqual(result["value"], 199.90)
        self.assertTrue(result["has_searchable_text"])
        self.assertTrue(result["ocr_used"])
        self.assertEqual(result["warning"], "")

    @patch("document_intelligence._ocr_scanned_pdf")
    @patch("document_intelligence._extract_pdf_text", return_value="")
    def test_scanned_pdf_falls_back_to_local_ocr(self, _extract, ocr):
        ocr.return_value = "NOTA FISCAL Número: 9988 Valor total R$ 450,00"
        result = analyze_document(b"%PDF", "application/pdf", "scan.pdf")
        self.assertEqual(result["category"], "Nota Fiscal")
        self.assertEqual(result["document_number"], "9988")
        self.assertTrue(result["ocr_used"])


if __name__ == "__main__":
    unittest.main()

