from psycopg.rows import dict_row

from .embeddings import to_pgvector_literal


def set_client_scope(conn, client_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config('app.current_client', %s, true)", (client_id,))


def search_clusters(conn, client_id: str, embedding: list[float], top_k: int) -> list[dict]:
    set_client_scope(conn, client_id)
    vector_literal = to_pgvector_literal(embedding)

    query = """
        SELECT
            id,
            client_id,
            text_content,
            codified_data,
            query_history,
            doc_count,
            last_updated,
            1 - (embedding <=> %(vector)s::vector) AS relevance_score
        FROM clusters
        WHERE client_id = %(client_id)s
        ORDER BY embedding <=> %(vector)s::vector
        LIMIT %(top_k)s
    """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            query,
            {
                "vector": vector_literal,
                "client_id": client_id,
                "top_k": top_k,
            },
        )
        return list(cur.fetchall())


def search_clusters_across_clients(
    conn,
    client_ids: list[str],
    embedding: list[float],
    top_k: int,
) -> list[dict]:
    combined: list[dict] = []
    for client_id in client_ids:
        combined.extend(search_clusters(conn, client_id, embedding, top_k))

    combined.sort(key=lambda row: float(row["relevance_score"]), reverse=True)
    return combined[:top_k]
