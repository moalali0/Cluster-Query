CREATE TABLE IF NOT EXISTS clusters (
    id UUID PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    text_content TEXT NOT NULL,

    codified_data JSONB,
    query_history JSONB,

    doc_count INTEGER,
    embedding VECTOR(384),
    embedding_model TEXT NOT NULL DEFAULT 'phase0-hash-v1',
    embedding_dim INTEGER NOT NULL DEFAULT 384,
    prompt_version TEXT NOT NULL DEFAULT 'phase0-prompt-v1',
    last_updated TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS cluster_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cluster_id UUID NOT NULL REFERENCES clusters(id) ON DELETE CASCADE,
    client_id VARCHAR(50) NOT NULL,
    actor_role VARCHAR(20) NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    event_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL DEFAULT gen_random_uuid(),
    client_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(120) NOT NULL,
    endpoint VARCHAR(64) NOT NULL,
    query_text TEXT,
    result_count INTEGER NOT NULL DEFAULT 0,
    evidence_found BOOLEAN NOT NULL DEFAULT FALSE,
    top_score REAL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
