"""Migracoes SQL do modulo careplanner (por tenant)."""
from __future__ import annotations

CAREPLANNER_MIGRATIONS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS care_tasks (
        id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        correlation_id       UUID NOT NULL UNIQUE,
        kestra_execution_id  TEXT,
        patient_ref          TEXT NOT NULL,
        task_type            TEXT NOT NULL,
        status               TEXT NOT NULL DEFAULT 'CREATED',
        channel              TEXT NOT NULL DEFAULT 'rocketchat',
        tenant_slug          TEXT NOT NULL,
        metadata             JSONB DEFAULT '{}',
        created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_care_tasks_status ON care_tasks(status, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_care_tasks_patient ON care_tasks(patient_ref, created_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS care_conversations (
        id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        correlation_id           UUID NOT NULL UNIQUE REFERENCES care_tasks(correlation_id),
        channel                  TEXT NOT NULL DEFAULT 'rocketchat',
        channel_conversation_id  BIGINT NOT NULL,
        rc_room_id               TEXT,
        phone_e164               TEXT,
        participant_role         TEXT,
        tenant_slug              TEXT NOT NULL,
        last_interaction_at      TIMESTAMPTZ,
        created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_care_conv_channel_id
        ON care_conversations(channel, channel_conversation_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS care_events (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        event_id       TEXT NOT NULL UNIQUE,
        correlation_id UUID REFERENCES care_tasks(correlation_id),
        event_type     TEXT NOT NULL,
        status         TEXT,
        payload        JSONB NOT NULL,
        tenant_slug    TEXT NOT NULL,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_care_events_corr ON care_events(correlation_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_care_events_type ON care_events(event_type, created_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS care_templates (
        id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        template_code TEXT NOT NULL,
        channel       TEXT NOT NULL DEFAULT 'rocketchat',
        content       TEXT NOT NULL,
        variables     JSONB DEFAULT '[]',
        active        BOOLEAN NOT NULL DEFAULT TRUE,
        tenant_slug   TEXT NOT NULL,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (template_code, channel, tenant_slug)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS care_video_sessions (
        id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        correlation_id UUID REFERENCES care_tasks(correlation_id),
        room_name      TEXT NOT NULL,
        clinico_jwt    TEXT NOT NULL,
        patient_jwt    TEXT NOT NULL,
        expires_at     TIMESTAMPTZ NOT NULL,
        clinico_ref    TEXT NOT NULL,
        patient_ref    TEXT NOT NULL,
        tenant_slug    TEXT NOT NULL,
        created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
]
