from __future__ import annotations

import unittest
from datetime import date

import pandas as pd

from assistant_query_engine import analyze_business_question
from assistant_resources import build_resource_bundle


class AssistantReportRequestTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 8, 26)
        self.transactions = pd.DataFrame([
            {"tx_date": "2025-12-20", "tx_type": "Receita", "description": "Projeto anterior", "category": "Serviços", "value": 900.0, "counterparty": "Cliente Alfa", "document_number": "N1", "payment_method": "PIX"},
            {"tx_date": "2026-07-10", "tx_type": "Receita", "description": "Projeto julho", "category": "Serviços", "value": 1500.0, "counterparty": "Cliente Alfa", "document_number": "N2", "payment_method": "PIX"},
            {"tx_date": "2026-08-02", "tx_type": "Receita", "description": "Projeto agosto", "category": "Serviços", "value": 2500.0, "counterparty": "Cliente Beta", "document_number": "N3", "payment_method": "PIX"},
            {"tx_date": "2026-08-15", "tx_type": "Receita", "description": "Projeto extra", "category": "Serviços", "value": 500.0, "counterparty": "Cliente Beta", "document_number": "N4", "payment_method": "Cartão"},
            {"tx_date": "2026-08-05", "tx_type": "Despesa", "description": "Insumos", "category": "Materiais", "value": 700.0, "counterparty": "Fornecedor X", "document_number": "D1", "payment_method": "PIX"},
            {"tx_date": "2026-08-18", "tx_type": "Despesa", "description": "Anúncios", "category": "Marketing", "value": 300.0, "counterparty": "Fornecedor Y", "document_number": "D2", "payment_method": "Cartão"},
        ])
        self.transactions["tx_date"] = pd.to_datetime(self.transactions["tx_date"])

    def ask(self, question: str):
        return analyze_business_question(question, self.transactions, today=self.today, default_year=2026)

    def test_generates_detailed_expense_report(self):
        result = self.ask("Gere um relatório das minhas despesas deste mês")
        self.assertEqual(result.kind, "transaction_report")
        self.assertEqual(len(result.table), 2)
        self.assertIn("1.000,00", result.summary)

    def test_generates_grouped_customer_and_supplier_reports(self):
        customers = self.ask("Mande o relatório dos meus clientes deste ano")
        suppliers = self.ask("Gere um relatório de fornecedores deste mês")
        self.assertEqual(customers.kind, "counterparty_report")
        self.assertEqual(customers.table.iloc[0]["Cliente"], "Cliente Beta")
        self.assertEqual(suppliers.table.iloc[0]["Fornecedor"], "Fornecedor X")

    def test_generates_daily_monthly_and_annual_revenue_timelines(self):
        daily = self.ask("Gere um relatório de faturamento diário deste mês")
        monthly = self.ask("Gere um relatório de faturamento mensal deste ano")
        annual = self.ask("Gere um relatório de faturamento anual")
        self.assertEqual(daily.kind, "revenue_timeline")
        self.assertEqual(len(daily.table), 2)
        self.assertEqual(list(monthly.table["Período"]), ["07/2026", "08/2026"])
        self.assertEqual(list(annual.table["Período"]), ["2025", "2026"])

    def test_generates_combined_financial_report(self):
        result = self.ask("Gere um relatório das minhas receitas e despesas deste mês")
        self.assertEqual(result.kind, "financial_report")
        self.assertEqual(len(result.table), 4)
        self.assertIn("resultado", result.summary)

    def test_resource_bundle_delivers_pdf_and_csv_in_chat(self):
        bundle = build_resource_bundle(
            "Gere um relatório de faturamento mensal deste ano",
            user_id=1,
            profile={},
            transactions=self.transactions,
            invoices=pd.DataFrame(),
            das_rows=[],
            obligations=[],
            documents=[],
            year=2026,
        )
        names = [item["file_name"] for item in bundle["downloads"]]
        self.assertIn("relatorio_faturamento_razync.csv", names)
        self.assertIn("relatorio_faturamento_razync.pdf", names)
        self.assertTrue(all(item["data"] for item in bundle["downloads"]))


if __name__ == "__main__":
    unittest.main()
