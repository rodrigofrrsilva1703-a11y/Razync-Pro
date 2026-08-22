import os
import subprocess
import sys
import unittest


class ProductionHardeningTests(unittest.TestCase):
    def _run_import(self, extra_env: dict[str, str]):
        env = os.environ.copy()
        for key in (
            "APP_ENVIRONMENT", "DATABASE_URL", "SUPABASE_DB_PASSWORD", "SUPABASE_DB_HOST",
            "SUPABASE_DB_USER", "SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SESSION_COOKIE_SECRET",
        ):
            env.pop(key, None)
        env.update(extra_env)
        return subprocess.run(
            [sys.executable, "-c", "import monitoring; print('ok')"],
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )

    def test_development_keeps_local_fallback_available(self):
        proc = self._run_import({"APP_ENVIRONMENT": "development"})
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)

    def test_production_refuses_unsafe_fallback(self):
        proc = self._run_import({"APP_ENVIRONMENT": "production"})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ProductionConfigurationError", proc.stderr)
        self.assertIn("modo de fallback", proc.stderr)

    def test_production_accepts_explicit_safe_configuration(self):
        proc = self._run_import({
            "APP_ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql+psycopg://user:pass@example.invalid:5432/postgres",
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
            "SESSION_COOKIE_SECRET": "x" * 48,
        })
        self.assertEqual(proc.returncode, 0, msg=proc.stdout + proc.stderr)
        self.assertIn("ok", proc.stdout)


if __name__ == "__main__":
    unittest.main()
