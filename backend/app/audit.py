from psycopg import Connection


def set_client_scope(conn: Connection, client_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.current_client', %s, true)", (client_id,))


def log_api_event(
    conn: Connection,
    *,
    client_id: str,
    user_id: str,
    endpoint: str,
    query_text: str,
    result_count: int,
    evidence_found: bool,
    top_score: float | None,
    status_code: int,
    response_time_ms: int,
    error_message: str | None = None,
) -> None:
    set_client_scope(conn, client_id)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO audit_logs (
                client_id,
                user_id,
                endpoint,
                query_text,
                result_count,
                evidence_found,
                top_score,
                status_code,
                response_time_ms,
                error_message
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                client_id,
                user_id,
                endpoint,
                query_text,
                result_count,
                evidence_found,
                top_score,
                status_code,
                response_time_ms,
                error_message,
            ),
        )
