from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATABASE_SOURCE = (ROOT / "database.py").read_text(encoding="utf-8")


class DatabasePoolResilienceTests(unittest.TestCase):
    def test_postgres_pool_checks_connections_before_checkout(self):
        self.assertIn('engine_kwargs: dict[str, Any] = {"pool_pre_ping": True}', DATABASE_SOURCE)

    def test_postgres_pool_recycles_connections_before_long_idle_sessions(self):
        self.assertIn('"pool_recycle": 240', DATABASE_SOURCE)
        self.assertNotIn('"pool_recycle": 1800', DATABASE_SOURCE)

    def test_postgres_connections_use_tcp_keepalives(self):
        for setting in ('"keepalives": 1', '"keepalives_idle": 60', '"keepalives_interval": 20', '"keepalives_count": 3'):
            self.assertIn(setting, DATABASE_SOURCE)

    def test_production_does_not_fallback_to_sqlite_after_connection_failure(self):
        self.assertIn('raise DatabaseConnectionError(_diagnose_operational_error(exc)) from None', DATABASE_SOURCE)


if __name__ == "__main__":
    unittest.main()
