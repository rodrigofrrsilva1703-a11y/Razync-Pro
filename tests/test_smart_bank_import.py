from io import BytesIO
import unittest

import pandas as pd

from bank_import import prepare_statement, read_statement, suggest_statement_columns


class _Upload(BytesIO):
    name = "extrato.csv"


class SmartBankImportTests(unittest.TestCase):
    def test_detects_common_bank_columns(self):
        frame = pd.DataFrame({
            "Data da transação": ["01/09/2026"],
            "Histórico": ["Cliente Alfa"],
            "Valor (R$)": ["1.250,00"],
        })
        self.assertEqual(suggest_statement_columns(frame), {
            "date": "Data da transação",
            "description": "Histórico",
            "value": "Valor (R$)",
        })

    def test_uploaded_csv_flows_into_normalized_preview(self):
        upload = _Upload("Data;Descrição;Valor\n01/09/2026;Venda;250,00\n".encode())
        raw = read_statement(upload)
        suggested = suggest_statement_columns(raw)
        prepared = prepare_statement(
            raw, suggested["date"], suggested["description"], suggested["value"]
        )
        self.assertEqual(list(prepared.columns), ["Data", "Tipo", "Descrição", "Valor"])
        self.assertEqual(prepared.iloc[0]["Tipo"], "Receita")
        self.assertEqual(float(prepared.iloc[0]["Valor"]), 250.0)


if __name__ == "__main__":
    unittest.main()
