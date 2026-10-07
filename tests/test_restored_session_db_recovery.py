from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DB = (ROOT / "database.py").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")


class DatabaseRecoveryTests(unittest.TestCase):
    def test_snapshot_discards_pool_and_retries_once(self):
        self.assertIn("def _dispose_stale_pool()", DB)
        self.assertIn("engine.dispose(close=False)", DB)
        block = DB[DB.index("def load_user_snapshot"):DB.index("def _hash_password")]
        self.assertGreaterEqual(block.count("_read_snapshot_from_postgres(user_id)"), 2)
        self.assertIn("_dispose_stale_pool()", block)

    def test_second_snapshot_failure_remains_fail_closed(self):
        block = DB[DB.index("def load_user_snapshot"):DB.index("def _hash_password")]
        self.assertIn(
            "raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None",
            block,
        )

    def test_recurring_maintenance_is_guarded_and_cannot_block_snapshot(self):
        recurring_pos = APP.index("materialize_due_recurring(uid)")
        snapshot_pos = APP.index("load_user_snapshot(uid)")
        self.assertLess(recurring_pos, snapshot_pos)
        self.assertIn("_recurring_check_key", APP)
        self.assertIn('"recurring_materialize_failed"', APP)
        self.assertIn("except DatabaseConnectionError:", APP)
        self.assertIn("generated_recurring = 0", APP)


if __name__ == "__main__":
    unittest.main()
