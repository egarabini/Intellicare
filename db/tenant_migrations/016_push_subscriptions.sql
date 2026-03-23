CREATE TABLE IF NOT EXISTS {schema}.push_subscriptions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES {schema}.users(id) ON DELETE CASCADE,
    endpoint     TEXT NOT NULL,
    p256dh       TEXT NOT NULL,
    auth         TEXT NOT NULL,
    user_agent   VARCHAR(255),
    created_at   TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ,
    UNIQUE(user_id, endpoint)
);
