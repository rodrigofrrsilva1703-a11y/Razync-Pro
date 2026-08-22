import os
import subprocess
import sys
import tempfile
import textwrap
import unittest


class UserIsolationIntegrationTests(unittest.TestCase):
    def test_two_users_cannot_read_or_mutate_each_others_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = os.path.join(tmp, "razync_isolation.db")
            code = textwrap.dedent(r'''
                import os
                from datetime import date
                os.environ["DATABASE_URL"] = "sqlite:///" + os.environ["TEST_DB_PATH"]
                import database as db

                db.init_db()
                for name, email in (("Conta A", "a@example.com"), ("Conta B", "b@example.com")):
                    ok, msg = db.create_user(name, email, "senha1234")
                    assert ok, msg
                user_a = db.authenticate("a@example.com", "senha1234")
                user_b = db.authenticate("b@example.com", "senha1234")
                a, b = int(user_a["id"]), int(user_b["id"])

                db.save_profile(a, business_name="Empresa A")
                db.save_profile(b, business_name="Empresa B")
                db.add_transaction(a, tx_date=date(2026,8,1), tx_type="Receita", description="Receita A", category="Serviços", value=100.0, document_number="A1", counterparty="Cliente A", payment_method="PIX")
                db.add_transaction(b, tx_date=date(2026,8,1), tx_type="Receita", description="Receita B", category="Serviços", value=200.0, document_number="B1", counterparty="Cliente B", payment_method="PIX")
                db.save_document(a, "a.pdf", "application/pdf", b"A", "Comprovante", "2026-08")
                db.save_document(b, "b.pdf", "application/pdf", b"B", "Comprovante", "2026-08")

                tx_a = db.list_transactions(a)
                tx_b = db.list_transactions(b)
                assert [row["description"] for row in tx_a] == ["Receita A"]
                assert [row["description"] for row in tx_b] == ["Receita B"]
                assert db.get_profile(a)["business_name"] == "Empresa A"
                assert db.get_profile(b)["business_name"] == "Empresa B"

                docs_a = db.list_documents(a)
                docs_b = db.list_documents(b)
                assert [row["filename"] for row in docs_a] == ["a.pdf"]
                assert [row["filename"] for row in docs_b] == ["b.pdf"]
                assert db.get_document(a, docs_b[0]["id"]) is None
                assert db.get_document(b, docs_a[0]["id"]) is None

                # Even with a foreign record id, mutation helpers must keep ownership scoped.
                assert not db.update_transaction(a, tx_b[0]["id"], description="INVASAO")
                db.delete_document(a, docs_b[0]["id"])
                assert db.list_transactions(b)[0]["description"] == "Receita B"
                assert db.get_document(b, docs_b[0]["id"])["content"] == b"B"

                snap_a = db.load_user_snapshot(a)
                snap_b = db.load_user_snapshot(b)
                assert all(row["description"] != "Receita B" for row in snap_a["transactions"])
                assert all(row["description"] != "Receita A" for row in snap_b["transactions"])
                assert all(row["filename"] != "b.pdf" for row in snap_a["documents"])
                assert all(row["filename"] != "a.pdf" for row in snap_b["documents"])
            ''')
            env = os.environ.copy()
            env["TEST_DB_PATH"] = db_path
            proc = subprocess.run([sys.executable, "-c", code], env=env, text=True, capture_output=True, timeout=60)
            self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)


if __name__ == "__main__":
    unittest.main()
