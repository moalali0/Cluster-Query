# Future Production Deployment (AWS Private Cloud)

## Recommended service split
- Inference node (GPU EC2): vLLM/llama.cpp only.
- API node (private EC2/ECS): auth, retrieval orchestration, audit API.
- Data node (RDS PostgreSQL + pgvector or dedicated Postgres EC2): metadata + vectors.

## Offline artifact supply chain
1. Build and scan container images in CI.
2. Push signed images to private ECR in `eu-west-2`.
3. Store approved model artifacts in private S3 bucket with KMS encryption.
4. Use VPC endpoints (S3, ECR API, ECR DKR, CloudWatch Logs, SSM).
5. Deny outbound internet/NAT from inference subnets.

## Tenant enforcement
- Identity claim -> `client_id` mapping at API boundary.
- API sets DB session variable `app.current_client`.
- RLS policies enforce in-database tenant isolation.
- API still includes explicit SQL `WHERE client_id = :client_id` defense-in-depth.

## Scheduling (Europe/London)
- 08:45 start compute.
- 09:30 run ingestion.
- 18:00 stop compute.
- Mon-Fri only.
