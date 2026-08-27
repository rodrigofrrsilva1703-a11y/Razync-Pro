from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

from table_ui import professional_table


class ProfessionalTableTests(unittest.TestCase):
    def test_table_uses_compact_rows_and_bounded_height(self):
        frame = pd.DataFrame({"Nome": [f"Item {index}" for index in range(20)]})
        with patch("table_ui.st.dataframe") as dataframe:
            professional_table(frame, max_visible_rows=8)
        kwargs = dataframe.call_args.kwargs
        self.assertEqual(kwargs["row_height"], 34)
        self.assertEqual(kwargs["height"], 310)
        self.assertTrue(kwargs["hide_index"])
        self.assertEqual(kwargs["width"], "stretch")

    def test_primary_workspaces_use_professional_table(self):
        for filename in ("dashboard_workspace.py", "finance_workspace.py", "fiscal_workspace.py"):
            source = Path(filename).read_text(encoding="utf-8")
            self.assertIn("professional_table(", source)


if __name__ == "__main__":
    unittest.main()
