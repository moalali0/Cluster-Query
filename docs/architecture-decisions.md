# Architecture Decisions Applied

## 1) Schedule conflict fixed
- EC2 start: 08:45 Europe/London
- Ingestion: 09:30 Europe/London
- EC2 stop: 18:00 Europe/London (Mon-Fri)

## 2) Tenant safety hardening
- RLS on `clusters` and `cluster_events`.
- App role restricted by `app.current_client`.
- Backend SQL still applies explicit `WHERE client_id = :client_id`.

## 3) Data model auditability
- Added `embedding_model`, `embedding_dim`, `prompt_version`.
- Added typed `cluster_events` table while keeping `query_history` JSONB.

## 4) Retrieval refusal contract
- If top matches are below `SIMILARITY_THRESHOLD`, API returns `evidence_found=false` and no answer.

## 5) Offline artifact flow (future production)
- Use private S3/ECR mirrors for model files and container images.
- No outbound internet from inference subnet.
