"""Migracoes SQL para tabelas de notificacoes (por tenant)."""
from __future__ import annotations

NOTIFICATION_MIGRATIONS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('appointment','clinical','system','message','alert')),
        priority TEXT NOT NULL DEFAULT 'normal'
            CHECK (priority IN ('low','normal','high','urgent')),
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        data JSONB DEFAULT '{}',
        read BOOLEAN NOT NULL DEFAULT FALSE,
        read_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id) WHERE read = FALSE",
    """
    CREATE TABLE IF NOT EXISTS notification_preferences (
        id SERIAL PRIMARY KEY,
        user_id TEXT NOT NULL UNIQUE,
        enabled BOOLEAN NOT NULL DEFAULT TRUE,
        types_enabled TEXT[] DEFAULT ARRAY['appointment','clinical','system','message','alert'],
        priority_min TEXT NOT NULL DEFAULT 'low'
            CHECK (priority_min IN ('low','normal','high','urgent')),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS push_subscriptions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        p256dh TEXT NOT NULL,
        auth TEXT NOT NULL,
        user_agent VARCHAR(255),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        last_used_at TIMESTAMPTZ,
        UNIQUE(user_id, endpoint)
    )
    """,
]
