CREATE INDEX IF NOT EXISTS idx_clusters_client_id ON clusters (client_id);
CREATE INDEX IF NOT EXISTS idx_clusters_last_updated ON clusters (last_updated DESC);
CREATE INDEX IF NOT EXISTS idx_clusters_embedding_hnsw
    ON clusters USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_clusters_codified_data_gin
    ON clusters USING gin (codified_data jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_cluster_events_cluster ON cluster_events (cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_events_client ON cluster_events (client_id);
CREATE INDEX IF NOT EXISTS idx_cluster_events_event_at ON cluster_events (event_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_client_created ON audit_logs (client_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_endpoint_created ON audit_logs (endpoint, created_at DESC);

GRANT SELECT ON clusters TO contract_ai_app;
GRANT SELECT ON cluster_events TO contract_ai_app;
GRANT SELECT, INSERT ON audit_logs TO contract_ai_app;
GRANT USAGE, SELECT ON SEQUENCE audit_logs_audit_id_seq TO contract_ai_app;

GRANT SELECT, INSERT, UPDATE, DELETE ON clusters TO contract_ai_ingest;
GRANT SELECT, INSERT, UPDATE, DELETE ON cluster_events TO contract_ai_ingest;
GRANT SELECT, INSERT, UPDATE, DELETE ON audit_logs TO contract_ai_ingest;
GRANT USAGE, SELECT ON SEQUENCE audit_logs_audit_id_seq TO contract_ai_ingest;

ALTER TABLE clusters ENABLE ROW LEVEL SECURITY;
ALTER TABLE cluster_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE clusters FORCE ROW LEVEL SECURITY;
ALTER TABLE cluster_events FORCE ROW LEVEL SECURITY;
ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS clusters_app_select ON clusters;
CREATE POLICY clusters_app_select ON clusters
    FOR SELECT TO contract_ai_app
    USING (client_id = current_setting('app.current_client', true));

DROP POLICY IF EXISTS cluster_events_app_select ON cluster_events;
CREATE POLICY cluster_events_app_select ON cluster_events
    FOR SELECT TO contract_ai_app
    USING (client_id = current_setting('app.current_client', true));

DROP POLICY IF EXISTS audit_logs_app_select ON audit_logs;
CREATE POLICY audit_logs_app_select ON audit_logs
    FOR SELECT TO contract_ai_app
    USING (client_id = current_setting('app.current_client', true));

DROP POLICY IF EXISTS audit_logs_app_insert ON audit_logs;
CREATE POLICY audit_logs_app_insert ON audit_logs
    FOR INSERT TO contract_ai_app
    WITH CHECK (client_id = current_setting('app.current_client', true));

DROP POLICY IF EXISTS clusters_ingest_all ON clusters;
CREATE POLICY clusters_ingest_all ON clusters
    FOR ALL TO contract_ai_ingest
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS cluster_events_ingest_all ON cluster_events;
CREATE POLICY cluster_events_ingest_all ON cluster_events
    FOR ALL TO contract_ai_ingest
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS audit_logs_ingest_all ON audit_logs;
CREATE POLICY audit_logs_ingest_all ON audit_logs
    FOR ALL TO contract_ai_ingest
    USING (true)
    WITH CHECK (true);
