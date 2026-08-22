from unittest.mock import patch
from pathlib import Path

from sqlalchemy import create_engine

import assistant_action_store as store


def test_action_key_is_claimed_only_once_and_returns_receipt():
    test_engine = create_engine("sqlite:///:memory:", future=True)
    with patch.object(store, "engine", test_engine), patch.object(store, "DATABASE_URL", "sqlite:///:memory:"):
        claimed, previous = store.claim_action(7, "unique-key", action_type="transaction", channel="web", summary="Despesa")
        assert claimed is True
        assert previous is None

        receipt = {"message": "Salvo", "action_type": "transaction", "record_id": 10}
        store.complete_action(7, "unique-key", receipt)
        claimed_again, previous = store.claim_action(7, "unique-key", action_type="transaction", channel="web", summary="Despesa")
        assert claimed_again is False
        assert previous == receipt


def test_action_history_is_scoped_by_user():
    test_engine = create_engine("sqlite:///:memory:", future=True)
    with patch.object(store, "engine", test_engine), patch.object(store, "DATABASE_URL", "sqlite:///:memory:"):
        store.claim_action(7, "user-seven", action_type="invoice", channel="web", summary="Nota 1")
        store.claim_action(8, "user-eight", action_type="transaction", channel="whatsapp", summary="Receita")
        assert [item["action_key"] for item in store.list_actions(7)] == ["user-seven"]


def test_production_migration_is_backend_only_and_idempotent():
    sql = Path("supabase/migrations/20260822021000_ai_action_executions.sql").read_text(encoding="utf-8").lower()
    assert "unique (user_id, action_key)" in sql
    assert "enable row level security" in sql
    assert "revoke all on table public.ai_action_executions from anon, authenticated" in sql
    assert "using (false)" in sql
    assert "with check (false)" in sql

