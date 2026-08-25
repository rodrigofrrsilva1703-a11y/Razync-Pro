from __future__ import annotations

import unittest

from assistant_history import (
    append_exchange,
    append_message,
    archive_conversation,
    create_conversation,
    list_conversations,
    load_messages,
)
from database import DATABASE_URL, create_user, engine, init_db
from sqlalchemy import text


@unittest.skipUnless(str(DATABASE_URL).startswith("sqlite"), "SQLite contract test")
class AssistantHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        email = "history-test@razync.local"
        create_user("History Test", email, "StrongPass123!")
        with engine.connect() as conn:
            cls.user_id = int(conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).scalar_one())

    def tearDown(self):
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM ai_messages WHERE user_id = :uid"), {"uid": self.user_id})
            conn.execute(text("DELETE FROM ai_conversations WHERE user_id = :uid"), {"uid": self.user_id})

    def test_persists_and_orders_messages(self):
        conversation_id = create_conversation(self.user_id)
        append_message(self.user_id, conversation_id, "user", "Registrar uma despesa de aluguel")
        append_message(self.user_id, conversation_id, "assistant", "Vou preparar para sua confirmação.")
        messages = load_messages(self.user_id, conversation_id)
        self.assertEqual([item["role"] for item in messages], ["user", "assistant"])
        self.assertEqual(list_conversations(self.user_id)[0]["title"], "Registrar uma despesa de aluguel")

    def test_persists_a_complete_exchange_atomically(self):
        conversation_id = create_conversation(self.user_id)
        append_exchange(
            self.user_id,
            conversation_id,
            "Quanto faturei?",
            "Você faturou R$ 1.000,00.",
            assistant_metadata={"resources": False},
        )
        messages = load_messages(self.user_id, conversation_id)
        self.assertEqual(messages, [
            {"role": "user", "content": "Quanto faturei?"},
            {"role": "assistant", "content": "Você faturou R$ 1.000,00."},
        ])
        self.assertEqual(list_conversations(self.user_id)[0]["title"], "Quanto faturei?")

    def test_user_cannot_read_another_users_conversation(self):
        conversation_id = create_conversation(self.user_id)
        append_message(self.user_id, conversation_id, "user", "Mensagem privada")
        self.assertEqual(load_messages(self.user_id + 999, conversation_id), [])

    def test_archived_conversation_is_hidden(self):
        conversation_id = create_conversation(self.user_id)
        archive_conversation(self.user_id, conversation_id)
        self.assertEqual(list_conversations(self.user_id), [])


if __name__ == "__main__":
    unittest.main()
