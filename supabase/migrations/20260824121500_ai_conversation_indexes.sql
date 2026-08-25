create index if not exists ix_ai_action_drafts_conversation
    on public.ai_action_drafts (conversation_id);

create index if not exists ix_ai_feedback_conversation
    on public.ai_feedback (conversation_id);
