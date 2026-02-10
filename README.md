# Secure Internal Contract AI (Phase 0 Skeleton)

This repo contains a local skeleton for a secure internal RAG system over contract cluster precedent data.

## What is implemented now
- FastAPI backend with strict client scoping.
- PostgreSQL 16 + pgvector schema.
- Row-Level Security (RLS) using session client context.
- API audit logging table with tenant-scoped access.
- Mock ingestion pipeline from CSV.
- React + Tailwind UI for search and result cards.
- Streaming chat endpoint contract (`text/event-stream`) with token events.
- "Insufficient evidence" refusal behavior.
- Automatic cross-bank retrieval (searches all configured bank streams by default).

## Security controls included in Phase 0
- App role (`contract_ai_app`) can only read rows where `client_id = app.current_client` (RLS).
- Ingestion role (`contract_ai_ingest`) is separate from app role.
- Backend enforces explicit client filter in SQL in addition to RLS.
- No external AI APIs are used.

## Quick start
1. `cp .env.example .env`
2. `docker compose up -d --build`
3. Generate mock data (50 rows):
   - `docker compose exec backend python scripts/generate_mock_csv.py`
4. Ingest mock data:
   - `docker compose exec backend python scripts/ingest_mock_csv.py --csv /data/mock_clusters.csv`
5. Open UI:
   - `http://localhost:5173`

## Helpful make targets
- `make up`
- `make generate`
- `make ingest`
- `make logs`
- `make down`

## API endpoints
- `GET /health`
- `POST /api/search`
- `POST /api/chat` (phase-0 summarizer with citations)
- `POST /api/chat/stream` (SSE events: `meta`, `token`, `done`)

`client_id` is intentionally not supported in API request payloads (requests with extra fields are rejected). The backend always searches all configured bank streams and returns a unified ranked result set.

## Audit query example
After running the stack:

`docker compose exec db psql -U postgres -d contract_ai -c "SELECT endpoint, client_id, result_count, evidence_found, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10;"`

## Production notes (future)
- Keep inference service and database on separate nodes.
- Use private artifact mirrors (ECR/S3) for offline model/image delivery.
- For AWS scheduling in `Europe/London`, ensure EC2 start time precedes ingestion trigger.
