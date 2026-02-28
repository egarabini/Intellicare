-- ══════════════════════════════════════════════════════════════════
-- IntelliCare NISE - Database Initialization
-- ══════════════════════════════════════════════════════════════════

-- Create schema
CREATE SCHEMA IF NOT EXISTS nise;

-- Set search path
SET search_path TO nise, public;

-- ── Chat Sessions ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_created_at ON chat_sessions(created_at);

-- ── Chat Messages ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_created_at ON chat_messages(created_at);

-- ── Cache Stats ───────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS cache_stats (
    stat_id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL,
    hit_count INTEGER DEFAULT 0,
    miss_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cache_stats_cache_key ON cache_stats(cache_key);

-- ── API Logs ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS api_logs (
    log_id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER,
    response_time_ms INTEGER,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_api_logs_endpoint ON api_logs(endpoint);
CREATE INDEX idx_api_logs_created_at ON api_logs(created_at);
CREATE INDEX idx_api_logs_user_id ON api_logs(user_id);

-- ── Flowise Chatflows ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS flowise_chatflows (
    chatflow_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Functions ─────────────────────────────────────────────────────

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers
CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_flowise_chatflows_updated_at
    BEFORE UPDATE ON flowise_chatflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ── Initial Data ──────────────────────────────────────────────────

-- Insert default chatflow
INSERT INTO flowise_chatflows (chatflow_id, name, description, config)
VALUES (
    'dr-nise-default',
    'Dr. Nise - Assistente Médico',
    'Chatbot padrão para treinamento médico e consultas FHIR',
    '{"model": "llama2:7b", "temperature": 0.7, "max_tokens": 2000}'::jsonb
) ON CONFLICT (chatflow_id) DO NOTHING;

-- ══════════════════════════════════════════════════════════════════
-- End of initialization
-- ══════════════════════════════════════════════════════════════════

