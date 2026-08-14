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
                db.save_profile(uid, business_name="MEI UI", trade_name="MEI UI", cnpj="12345678000100", main_activity="Serviços", opening_date=date(2026,1,1), has_employee=True)
                db.add_transaction(uid, tx_date=date(2026,8,1), tx_type="Receita", description="Venda", category="Serviços", value=1000.0, document_number="NF1", counterparty="Cliente", payment_method="PIX")
                db.add_transaction(uid, tx_date=date(2026,8,2), tx_type="Despesa", description="Material", category="Materiais", value=200.0, document_number="C1", counterparty="Fornecedor", payment_method="PIX")
                db.add_invoice(uid, issue_date=date(2026,8,1), invoice_type="Serviço", number="NF1", customer="Cliente", customer_document="", description="Serviço", amount=1000.0, status="Emitida")
                db.upsert_das(uid, "2026-08", date(2026,9,21), 80.0, "Pendente", None, "")
                db.save_document(uid, "comprovante.pdf", "application/pdf", b"arquivo", "Comprovante", "2026-08")
                db.add_contact(uid, contact_type="Cliente", name="Cliente", document="", email="cliente@example.com", phone="", notes="")
                db.add_employee(uid, name="Pessoa", cpf="", admission_date=date(2026,8,1), salary=1500.0, status="Ativo", notes="")
                db.add_obligation(uid, title="Obrigação teste", due_date=date(2026,8,30), status="Pendente", category="Fiscal", notes="")
                db.add_recurring_transaction(uid, tx_type="Despesa", description="Internet", category="Taxas", value=100.0, payment_method="PIX", frequency="Mensal", next_date=date(2027,1,1), end_date=None, active=True)

                from streamlit.testing.v1 import AppTest
                from product_core import NAV_GROUPS

                pages = [p for group in NAV_GROUPS.values() for p in group]
                for page in pages:
                    at = AppTest.from_file("app.py", default_timeout=25)
                    at.session_state["user"] = user
                    at.session_state["_current_page"] = page
                    at.run()
                    errors = [str(x.value) for x in at.exception]
                    assert not errors, f"Pagina {page} falhou: {errors}"
            ''')
            env = os.environ.copy()
            env["TEST_DB_PATH"] = db_path
            proc = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, timeout=240)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)


if __name__ == "__main__":
    unittest.main()
