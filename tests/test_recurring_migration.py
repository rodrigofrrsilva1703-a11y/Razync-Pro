import unittest
from pathlib import Path


class RecurringMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = (
            Path(__file__).resolve().parents[1]
            / "supabase"
            / "migrations"
            / "20260814033500_recurring_transactions.sql"
        ).read_text(encoding="utf-8").lower()

    def test_table_has_rls_owner_policy_and_explicit_grants(self):
        self.assertIn("alter table public.recurring_transactions enable row level security", self.sql)
        self.assertIn("to authenticated", self.sql)
        self.assertIn("u.auth_user_id = (select auth.uid())", self.sql)
        self.assertIn("with check", self.sql)
        self.assertIn("grant select, insert, update, delete", self.sql)

    def test_ownership_and_due_date_columns_are_indexed(self):
        self.assertIn("recurring_transactions_user_id_idx", self.sql)
        self.assertIn("recurring_transactions_due_idx", self.sql)
        self.assertIn("transactions_recurring_date_uidx", self.sql)

    def test_recurring_generated_transactions_are_idempotent(self):
        self.assertIn("unique index", self.sql)
        self.assertIn("(recurring_transaction_id, tx_date)", self.sql)


if __name__ == "__main__":
    unittest.main()
