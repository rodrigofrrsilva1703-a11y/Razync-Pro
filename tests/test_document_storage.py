import unittest
from pathlib import Path

from storage_service import _safe_filename


class DocumentStorageTests(unittest.TestCase):
    def test_filename_cannot_escape_user_folder(self):
        self.assertEqual(_safe_filename("../../contrato final.pdf"), "contrato_final.pdf")
        self.assertEqual(_safe_filename(r"..\\..\\arquivo.exe"), "arquivo.exe")

    def test_application_keeps_legacy_fallback(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "app.py").read_text(encoding="utf-8")
        self.assertIn("upload_document(", source)
        self.assertIn("download_document(", source)
        self.assertIn("remove_document(", source)
        self.assertIn('document.get("content") or b""', source)


if __name__ == "__main__":
    unittest.main()
