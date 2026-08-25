from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine

import assistant_state_store as store


class AssistantStateStoreTests(unittest.TestCase):
    def test_persists_updates_and_closes_a_pending_draft(self):
        test_engine = create_engine("sqlite:///:memory:", future=True)
        draft = {"action_key": "draft-1", "action_type": "transaction", "channel": "web", "summary": "Despesa", "payload": {"value": 10}}
        with patch.object(store, "engine", test_engine), patch.object(store, "DATABASE_URL", "sqlite:///:memory:"):
            store.save_draft(7, draft)
            draft["summary"] = "Despesa revisada"
            store.save_draft(7, draft)
            pending = store.list_pending_drafts(7)
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["summary"], "Despesa revisada")
            store.set_draft_status(7, "draft-1", "confirmed")
            self.assertEqual(store.list_pending_drafts(7), [])

    def test_feedback_is_idempotent_for_the_same_answer(self):
        test_engine = create_engine("sqlite:///:memory:", future=True)
        with patch.object(store, "engine", test_engine), patch.object(store, "DATABASE_URL", "sqlite:///:memory:"):
            store.save_feedback(7, "Resposta", True)
            store.save_feedback(7, "Resposta", False)
            with test_engine.connect() as conn:
                row = conn.exec_driver_sql("select count(*), helpful from ai_feedback").first()
            self.assertEqual(row[0], 1)
            self.assertEqual(row[1], 0)

    def test_migration_keeps_ai_tables_backend_only(self):
        sql = Path("supabase/migrations/20260824120000_ai_approval_and_feedback.sql").read_text(encoding="utf-8").lower()
        self.assertIn("alter table public.ai_action_drafts enable row level security", sql)
        self.assertIn("revoke all on table public.ai_feedback from anon, authenticated", sql)
        self.assertIn("using (false) with check (false)", sql)


if __name__ == "__main__":
    unittest.main()
