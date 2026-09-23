from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DB = (ROOT / "database.py").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")

class RestoredSessionDatabaseRecoveryTests(unittest.TestCase):
    def test_snapshot_discards_pool_and_retries_once(self):
        self.assertIn("def _dispose_stale_pool()", DB)
        self.assertIn("engine.dispose(close=False)", DB)
        block = DB[DB.index("def load_user_snapshot"):DB.index("def _hash_password")]
        self.assertGreaterEqual(block.count("_read_snapshot_from_postgres(user_id)"), 2)
        self.assertIn("_dispose_stale_pool()", block)

    def test_second_snapshot_failure_remains_fail_closed(self):
        block = DB[DB.index("def load_user_snapshot"):DB.index("def _hash_password")]
        self.assertIn("raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None", block)

    def test_recurring_maintenance_cannot_block_restored_session_snapshot(self):
        self.assertIn('safe_error("recurring_materialize_failed"', APP)
        self.assertIn("generated_recurring = 0", APP)
        self.assertLess(APP.index("materialize_due_recurring(uid)"), APP.index("load_user_snapshot(uid)"))

if __name__ == "__main__":
    unittest.main()
