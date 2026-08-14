from pathlib import Path
import unittest

class AtomicImportTests(unittest.TestCase):
    def test_import_uses_one_database_transaction(self):
        db=Path("database.py").read_text(encoding="utf-8")
        app=Path("app.py").read_text(encoding="utf-8")
        start=db.index("def add_transactions_bulk")
        body=db[start:]
        self.assertIn("with engine.begin() as conn:",body)
        self.assertIn("conn.execute(insert(transactions), prepared)",body)
        self.assertIn("add_transactions_bulk(uid,import_rows)",app)
        self.assertIn("nenhum lançamento foi salvo",app)
        old_loop='for _,r in rows_to_import.iterrows():\n                            add_transaction'
        self.assertNotIn(old_loop,app)

if __name__=="__main__":
    unittest.main()
