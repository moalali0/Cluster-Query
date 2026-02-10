import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import get_ingest_conn
from app.embeddings import embed_text, to_pgvector_literal

UPSERT_CLUSTER = """
INSERT INTO clusters (
    id,
    client_id,
    text_content,
    codified_data,
    query_history,
    doc_count,
    embedding,
    embedding_model,
    embedding_dim,
    prompt_version,
    last_updated
)
VALUES (
    %(id)s,
    %(client_id)s,
    %(text_content)s,
    %(codified_data)s::jsonb,
    %(query_history)s::jsonb,
    %(doc_count)s,
    %(embedding)s::vector,
    %(embedding_model)s,
    %(embedding_dim)s,
    %(prompt_version)s,
    %(last_updated)s
)
ON CONFLICT (id)
DO UPDATE SET
    client_id = EXCLUDED.client_id,
    text_content = EXCLUDED.text_content,
    codified_data = EXCLUDED.codified_data,
    query_history = EXCLUDED.query_history,
    doc_count = EXCLUDED.doc_count,
    embedding = EXCLUDED.embedding,
    embedding_model = EXCLUDED.embedding_model,
    embedding_dim = EXCLUDED.embedding_dim,
    prompt_version = EXCLUDED.prompt_version,
    last_updated = EXCLUDED.last_updated
"""

DELETE_EVENTS = "DELETE FROM cluster_events WHERE cluster_id = %(cluster_id)s"
INSERT_EVENT = """
INSERT INTO cluster_events (
    cluster_id,
    client_id,
    actor_role,
    event_type,
    message,
    event_at
)
VALUES (
    %(cluster_id)s,
    %(client_id)s,
    %(actor_role)s,
    %(event_type)s,
    %(message)s,
    %(event_at)s
)
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest mock cluster CSV into Postgres")
    parser.add_argument("--csv", required=True, help="Path to mock CSV")
    parser.add_argument("--batch-size", type=int, default=1000)
    return parser.parse_args()


def to_event_rows(cluster_id: str, client_id: str, history: list[dict]) -> list[dict]:
    event_rows: list[dict] = []
    for entry in history:
        role = entry.get("role", "Unknown")
        if "query" in entry:
            event_type = "query"
            message = entry["query"]
        else:
            event_type = "response"
            message = entry.get("response", "")
        event_rows.append(
            {
                "cluster_id": cluster_id,
                "client_id": client_id,
                "actor_role": role,
                "event_type": event_type,
                "message": message,
                "event_at": datetime.fromisoformat(entry["date"] + "T00:00:00+00:00"),
            }
        )
    return event_rows


def main() -> None:
    args = parse_args()

    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with get_ingest_conn() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(rows), args.batch_size):
                batch = rows[i : i + args.batch_size]
                for row in batch:
                    embedding = embed_text(row["text_content"])
                    cur.execute(
                        UPSERT_CLUSTER,
                        {
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
                        },
                    )

                    history = json.loads(row["query_history"])
                    cur.execute(DELETE_EVENTS, {"cluster_id": row["id"]})
                    for event in to_event_rows(row["id"], row["client_id"], history):
                        cur.execute(INSERT_EVENT, event)

            conn.commit()

    print(f"Ingested {len(rows)} rows from {args.csv}")


if __name__ == "__main__":
    main()
