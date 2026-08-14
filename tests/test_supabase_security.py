import unittest
from pathlib import Path


class SupabaseSecurityMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.migration = (
            root
            / "supabase"
            / "migrations"
            / "20260814004808_secure_auth_rls_and_document_storage.sql"
        ).read_text(encoding="utf-8").lower()

    def test_snapshot_is_not_public_or_security_definer(self):
        self.assertIn(
            "revoke all on function public.razync_user_snapshot(bigint)",
            self.migration,
        )
        self.assertIn(
            "alter function public.razync_user_snapshot(bigint) security invoker",
            self.migration,
        )

    def test_every_business_table_has_owner_policy(self):
        for table in (
            "mei_profiles",
            "transactions",
            "das_items",
            "documents",
            "invoices",
            "contacts",
            "employees",
            "obligations",
        ):
            with self.subTest(table=table):
                self.assertIn(f"'{table}'", self.migration)

        self.assertIn("u.auth_user_id = (select auth.uid())", self.migration)
        self.assertIn("with check", self.migration)

    def test_document_bucket_is_private_and_supports_all_mutations(self):
        self.assertIn("values ('documents', 'documents', false)", self.migration)
        for operation in ("select", "insert", "update", "delete"):
            self.assertIn(f"documents_storage_{operation}", self.migration)


if __name__ == "__main__":
    unittest.main()
