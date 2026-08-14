from pathlib import Path
import unittest

class AuditCenterTests(unittest.TestCase):
    def test_navigation_and_owner_scoped_query_exist(self):
        app=Path("app.py").read_text(encoding="utf-8")
        core=Path("product_core.py").read_text(encoding="utf-8")
        db=Path("database.py").read_text(encoding="utf-8")
        self.assertIn("Histórico de Atividades",core)
        self.assertIn('elif page == "Histórico de Atividades":',app)
        self.assertIn("list_audit_logs(uid,250)",app)
        self.assertIn(".where(audit_logs.c.user_id == user_id)",db)
        self.assertIn("min(int(limit), 500)",db)
        self.assertIn("senhas e conteúdo binário",app)

if __name__=="__main__":
    unittest.main()
