"""One-time DB setup for cloud deployments (Render, Railway).

Creates extensions, schema, indexes, and seeds mock data.
Skips role creation and RLS (cloud platforms provide a single DB role).
"""

import csv
import json
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings
from app.embeddings import embed_text, to_pgvector_literal

SCHEMA_SQL = """
-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Tables
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_clusters_client_id ON clusters (client_id);
CREATE INDEX IF NOT EXISTS idx_clusters_last_updated ON clusters (last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_clusters_embedding_hnsw
    ON clusters USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_clusters_codified_data_gin
    ON clusters USING gin (codified_data jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_cluster_events_cluster ON cluster_events (cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_events_client ON cluster_events (client_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_client_created ON audit_logs (client_id, created_at DESC);
"""

UPSERT_CLUSTER = """
INSERT INTO clusters (
    id, client_id, text_content, codified_data, query_history,
    doc_count, embedding, embedding_model, embedding_dim, prompt_version, last_updated
) VALUES (
    %(id)s, %(client_id)s, %(text_content)s, %(codified_data)s::jsonb,
    %(query_history)s::jsonb, %(doc_count)s, %(embedding)s::vector,
    %(embedding_model)s, %(embedding_dim)s, %(prompt_version)s, %(last_updated)s
)
ON CONFLICT (id) DO UPDATE SET
    text_content = EXCLUDED.text_content,
    codified_data = EXCLUDED.codified_data,
    query_history = EXCLUDED.query_history,
    embedding = EXCLUDED.embedding,
    last_updated = EXCLUDED.last_updated
"""

INSERT_EVENT = """
INSERT INTO cluster_events (cluster_id, client_id, actor_role, event_type, message, event_at)
VALUES (%(cluster_id)s, %(client_id)s, %(actor_role)s, %(event_type)s, %(message)s, %(event_at)s)
ON CONFLICT DO NOTHING
"""


def seed_data(conn) -> int:
    """Seed clusters from the mock CSV. Returns row count."""
    csv_path = Path(__file__).resolve().parents[1] / "data" / "mock_clusters.csv"
    if not csv_path.exists():
        print(f"  No seed data found at {csv_path}, skipping.")
        return 0

    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with conn.cursor() as cur:
        for row in rows:
            embedding = embed_text(row["text_content"])
            cur.execute(UPSERT_CLUSTER, {
                "id": row["id"],
                "client_id": row["client_id"],
                "text_content": row["text_content"],
                "codified_data": row["codified_data"],
                "query_history": row["query_history"],
                "doc_count": int(row["doc_count"]),
                "embedding": to_pgvector_literal(embedding),
                "embedding_model": "phase0-hash-v1",
                "embedding_dim": 384,
                "prompt_version": "phase0-prompt-v1",
                "last_updated": row["last_updated"],
            })

            # Seed query history as events
            history = json.loads(row["query_history"])
            from datetime import datetime
            for entry in history:
                role = entry.get("role", "Unknown")
                msg = entry.get("query") or entry.get("response", "")
                event_type = "query" if "query" in entry else "response"
                cur.execute(INSERT_EVENT, {
                    "cluster_id": row["id"],
                    "client_id": row["client_id"],
                    "actor_role": role,
                    "event_type": event_type,
                    "message": msg,
                    "event_at": datetime.fromisoformat(entry["date"] + "T00:00:00+00:00"),
                })

    conn.commit()
    return len(rows)


def main():
    db_url = settings.ingest_database_url
    print(f"Cloud DB setup: connecting to {db_url[:40]}...")

    with psycopg.connect(db_url, autocommit=False) as conn:
        # 1. Create schema
        print("  Creating schema + indexes...")
        conn.execute(SCHEMA_SQL)
        conn.commit()

        # 2. Seed data
        print("  Seeding mock data...")
        count = seed_data(conn)
        print(f"  Seeded {count} clusters.")

    print("Cloud DB setup complete.")


if __name__ == "__main__":
    main()
