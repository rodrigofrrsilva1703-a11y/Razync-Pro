from pathlib import Path
import unittest


class AtomicImportTests(unittest.TestCase):
    def test_import_uses_one_database_transaction(self):
        db = Path("database.py").read_text(encoding="utf-8")
        app = Path("app.py").read_text(encoding="utf-8")
        start = db.index("def add_transactions_bulk")
        body = db[start:]
        self.assertIn("with engine.begin() as conn:", body)
        self.assertIn("conn.execute(insert(transactions), prepared)", body)

        compact_app = "".join(app.split())
        self.assertIn("add_transactions_bulk(uid,import_rows)", compact_app)
        self.assertIn("nenhum lançamento foi salvo", app)
        self.assertNotIn(
            'for_,rinrows_to_import.iterrows():add_transaction',
            compact_app,
        )


if __name__ == "__main__":
    unittest.main()
