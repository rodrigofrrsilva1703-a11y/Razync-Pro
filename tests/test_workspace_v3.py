from pathlib import Path
import unittest

import navigation_config


class WorkspaceV3Tests(unittest.TestCase):
    def test_primary_navigation_is_reduced(self):
        visible = [item for group in navigation_config.SIDEBAR_GROUPS.values() for item in group]
        self.assertIn("Financeiro", visible)
        self.assertIn("Fiscal", visible)
        self.assertNotIn("Recorrências", visible)
        self.assertNotIn("Importar NFS-e", visible)

    def test_detailed_routes_remain_available(self):
        secondary = [item for group in navigation_config.SIDEBAR_SECONDARY_GROUPS.values() for item in group]
        for route in [
            "Movimentações", "Recorrências", "Importar Extrato", "Conciliação",
            "Fluxo de Caixa", "Análise Financeira", "DAS", "Notas Fiscais",
            "Importar NFS-e", "Obrigações", "DASN-SIMEI", "Fechamento Mensal",
            "Relatório Mensal", "Empregado", "Espaço do Contador",
        ]:
            self.assertIn(route, secondary)

    def test_workspace_modules_are_separate_from_app(self):
        self.assertTrue(Path("finance_workspace.py").exists())
        self.assertTrue(Path("fiscal_workspace.py").exists())
        self.assertTrue(Path("workspace_style.py").exists())


if __name__ == "__main__":
    unittest.main()
