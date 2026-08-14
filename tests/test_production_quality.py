import unittest
from pathlib import Path


class ProductionQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.database_source = (cls.root / "database.py").read_text(encoding="utf-8")
        cls.requirements = (cls.root / "requirements.txt").read_text(encoding="utf-8")

    def test_monetary_columns_use_exact_numeric_type(self):
        for column in ("annual_limit", "value", "amount", "salary"):
            with self.subTest(column=column):
                self.assertRegex(
                    self.database_source,
                    rf'Column\("{column}", Numeric\(14, 2\)',
                )

    def test_supabase_dependency_is_pinned(self):
        self.assertIn("supabase==2.31.0", self.requirements)
        self.assertNotIn("supabase>=", self.requirements)

    def test_no_secret_key_is_committed(self):
        for path in self.root.rglob("*"):
            if not path.is_file() or ".git" in path.parts:
                continue
            if path.suffix.lower() not in {".py", ".md", ".toml", ".yml", ".example"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            self.assertNotIn("sb_secret_", text, str(path))


if __name__ == "__main__":
    unittest.main()
