import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

import pandas as pd

import auth_service
from backup_tools import backup_checksum, build_backup_zip


class ProductImprovementTests(unittest.TestCase):
    def test_backup_contains_manifest_and_loaded_documents(self):
        payload = build_backup_zip(
            {"name": "MEI"}, pd.DataFrame([{"id": 1}]), pd.DataFrame(), [], [], [], [],
            [{"id": 7, "filename": "nota.pdf"}],
            lambda _document_id: {"content": b"pdf-content"},
        )
        with ZipFile(io.BytesIO(payload)) as archive:
            self.assertIn("manifesto.json", archive.namelist())
            self.assertIn("documentos/7-nota.pdf", archive.namelist())
        self.assertEqual(len(backup_checksum(payload)), 64)

    def test_password_change_restores_session_before_update(self):
        auth = SimpleNamespace()
        auth.set_session = unittest.mock.Mock()
        auth.update_user = unittest.mock.Mock(return_value=SimpleNamespace(user=object()))
        with patch("auth_service._client", return_value=SimpleNamespace(auth=auth)):
            auth_service.update_password("access", "refresh", "nova-senha-segura")
        auth.set_session.assert_called_once_with("access", "refresh")
        auth.update_user.assert_called_once_with({"password": "nova-senha-segura"})

    def test_short_password_is_rejected_before_network_call(self):
        with self.assertRaises(auth_service.AuthServiceError):
            auth_service.update_password("access", "refresh", "curta")


if __name__ == "__main__":
    unittest.main()
