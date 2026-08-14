import os
import subprocess
import sys
import tempfile
import textwrap
import unittest


class StreamlitPageSmokeTests(unittest.TestCase):
    def test_every_authenticated_page_renders_without_exception(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "razync_pages.db")
            code = textwrap.dedent(r'''
                import os
                from datetime import date
                os.environ["DATABASE_URL"] = "sqlite:///" + os.environ["TEST_DB_PATH"]
                import database as db
                db.init_db()
                ok, msg = db.create_user("Teste UI", "ui@example.com", "senha1234")
                assert ok, msg
                user = db.authenticate("ui@example.com", "senha1234")
                uid = int(user["id"])
                db.save_profile(uid, business_name="MEI UI", trade_name="MEI UI", cnpj="12345678000100", main_activity="Serviços", opening_date=date(2026,1,1))
                db.add_transaction(uid, tx_date=date(2026,8,1), tx_type="Receita", description="Venda", category="Serviços", value=100.0, document_number="", counterparty="Cliente", payment_method="PIX")

                from streamlit.testing.v1 import AppTest
                from product_core import NAV_GROUPS

                pages = [p for group in NAV_GROUPS.values() for p in group]
                for page in pages:
                    at = AppTest.from_file("app.py", default_timeout=20)
                    at.session_state["user"] = user
                    at.session_state["_current_page"] = page
                    at.run()
                    errors = [str(x.value) for x in at.exception]
                    assert not errors, f"Pagina {page} falhou: {errors}"
            ''')
            env = os.environ.copy()
            env["TEST_DB_PATH"] = db_path
            proc = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, timeout=180)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)


if __name__ == "__main__":
    unittest.main()
