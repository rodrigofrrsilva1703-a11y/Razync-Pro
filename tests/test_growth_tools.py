from datetime import date
import unittest

import pandas as pd

from growth_tools import build_notifications, checkout_url, normalize_nfse, notification_calendar, suggest_nfse_columns


class GrowthToolsTests(unittest.TestCase):
    def test_notifications_prioritize_overdue_das(self):
        items = build_notifications([{"competence": "2026-07", "due_date": date(2026, 8, 10), "status": "Pendente"}], [], 0, 81000, today=date(2026, 8, 15))
        self.assertEqual(items[0]["level"], "urgent")
        self.assertIn("DAS", items[0]["title"])

    def test_calendar_contains_only_dated_items(self):
        data = notification_calendar([
            {"title": "DAS", "detail": "Prazo", "due_date": date(2026, 8, 20)},
            {"title": "Limite", "detail": "Aviso", "due_date": None},
        ], "https://example.com")
        text = data.decode("utf-8")
        self.assertEqual(text.count("BEGIN:VEVENT"), 1)
        self.assertIn("DTSTART;VALUE=DATE:20260820", text)

    def test_nfse_column_suggestions(self):
        columns = suggest_nfse_columns(["Data Emissão", "Número NFS-e", "Tomador", "Valor Líquido"])
        self.assertEqual(columns["date"], "Data Emissão")
        self.assertEqual(columns["amount"], "Valor Líquido")

    def test_checkout_rejects_non_https(self):
        self.assertEqual(checkout_url({"CHECKOUT_PRO_URL": "http://unsafe.test"}, "pro"), "")
        self.assertEqual(checkout_url({"CHECKOUT_PRO_URL": "https://pay.test"}, "pro"), "https://pay.test")

    def test_nfse_normalization_skips_invalid_rows(self):
        frame = pd.DataFrame([
            {"Data": "15/08/2026", "Número": "42", "Valor": "R$ 1.250,50", "Situação": "Emitida"},
            {"Data": "", "Número": "43", "Valor": "100", "Situação": "Emitida"},
        ])
        rows = normalize_nfse(frame, {"date": "Data", "number": "Número", "amount": "Valor", "status": "Situação"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amount"], 1250.5)


if __name__ == "__main__":
    unittest.main()
