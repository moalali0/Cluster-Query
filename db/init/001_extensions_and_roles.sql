CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'contract_ai_app') THEN
        CREATE ROLE contract_ai_app LOGIN PASSWORD 'contract_ai_app';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'contract_ai_ingest') THEN
        CREATE ROLE contract_ai_ingest LOGIN PASSWORD 'contract_ai_ingest';
    END IF;
END $$;

GRANT CONNECT ON DATABASE contract_ai TO contract_ai_app;
GRANT CONNECT ON DATABASE contract_ai TO contract_ai_ingest;
GRANT USAGE ON SCHEMA public TO contract_ai_app;
GRANT USAGE ON SCHEMA public TO contract_ai_ingest;
