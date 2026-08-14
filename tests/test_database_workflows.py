import os
import subprocess
import sys
import tempfile
import textwrap
import unittest


class DatabaseWorkflowIntegrationTests(unittest.TestCase):
    def test_all_core_crud_and_snapshot_on_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "razync_test.db")
            code = textwrap.dedent(r'''
                import os
                from datetime import date
                os.environ["DATABASE_URL"] = "sqlite:///" + os.environ["TEST_DB_PATH"]
                import database as db

                db.init_db()
                ok, msg = db.create_user("Teste", "teste@example.com", "senha1234")
                assert ok, msg
                user = db.authenticate("teste@example.com", "senha1234")
                assert user and user["id"]
                uid = int(user["id"])

                db.save_profile(uid, business_name="MEI Teste", cnpj="123", main_activity="Serviços", opening_date=date(2026,1,1))
                assert db.get_profile(uid)["business_name"] == "MEI Teste"

                db.add_transaction(uid, tx_date=date(2026,8,1), tx_type="Receita", description="Venda", category="Serviços", value=100.0, document_number="N1", counterparty="Cliente", payment_method="PIX")
                tx = db.list_transactions(uid)
                assert len(tx) == 1
                assert db.update_transaction(uid, tx[0]["id"], description="Venda ajustada")
                assert db.list_transactions(uid)[0]["description"] == "Venda ajustada"

                db.add_recurring_transaction(uid, tx_type="Despesa", description="Internet", category="Taxas", value=50.0, payment_method="PIX", frequency="Mensal", next_date=date(2026,8,1), end_date=None, active=True)
                assert db.materialize_due_recurring(uid, today=date(2026,8,14)) == 1
                assert db.materialize_due_recurring(uid, today=date(2026,8,14)) == 0

                db.upsert_das(uid, "2026-08", date(2026,9,21), 80.0, "Pendente", None, "")
                assert len(db.list_das(uid)) == 1

                db.save_document(uid, "teste.pdf", "application/pdf", b"abc", "DAS", "2026-08")
                docs = db.list_documents(uid)
                assert len(docs) == 1
                full_doc = db.get_document(uid, docs[0]["id"])
                assert full_doc and full_doc["content"] == b"abc"

                db.add_invoice(uid, issue_date=date(2026,8,2), invoice_type="Serviço", number="1", customer="Cliente", customer_document="", description="Serviço", amount=100.0, status="Emitida")
                db.add_contact(uid, contact_type="Cliente", name="Cliente", document="", email="", phone="", notes="")
                db.add_employee(uid, name="Pessoa", cpf="", admission_date=date(2026,8,1), salary=1500.0, status="Ativo", notes="")
                db.add_obligation(uid, title="Tarefa", due_date=date(2026,8,20), status="Pendente", category="Fiscal", notes="")

                assert len(db.list_invoices(uid)) == 1
                assert len(db.list_contacts(uid)) == 1
                assert len(db.list_employees(uid)) == 1
                assert len(db.list_obligations(uid)) == 1

                snapshot = db.load_user_snapshot(uid)
                assert snapshot["profile"]["business_name"] == "MEI Teste"
                assert len(snapshot["transactions"]) >= 2
                assert len(snapshot["invoices"]) == 1
                assert len(snapshot["das"]) == 1
                assert len(snapshot["documents"]) == 1
                assert len(snapshot["contacts"]) == 1
                assert len(snapshot["employees"]) == 1
                assert len(snapshot["obligations"]) == 1

                db.delete_invoice(uid, db.list_invoices(uid)[0]["id"])
                db.delete_contact(uid, db.list_contacts(uid)[0]["id"])
                db.delete_employee(uid, db.list_employees(uid)[0]["id"])
                oid = db.list_obligations(uid)[0]["id"]
                db.update_obligation_status(uid, oid, "Concluído")
                assert db.list_obligations(uid)[0]["status"] == "Concluído"
                db.delete_obligation(uid, oid)
                db.delete_document(uid, docs[0]["id"])
                for row in list(db.list_transactions(uid)):
                    db.delete_transaction(uid, row["id"])

                assert db.list_invoices(uid) == []
                assert db.list_contacts(uid) == []
                assert db.list_employees(uid) == []
                assert db.list_obligations(uid) == []
                assert db.list_documents(uid) == []
                assert db.list_transactions(uid) == []
            ''')
            env = os.environ.copy()
            env["TEST_DB_PATH"] = db_path
            proc = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)


if __name__ == "__main__":
    unittest.main()
