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


def search_clusters_structured(
    conn,
    client_id: str,
    top_k: int,
    term: str | None = None,
    attribute: str | None = None,
    embedding: list[float] | None = None,
) -> list[dict]:
    """Structured search combining JSONB filters with optional embedding similarity."""
    set_client_scope(conn, client_id)

    conditions = ["client_id = %(client_id)s"]
    params: dict = {"client_id": client_id, "top_k": top_k}

    if term and attribute:
        conditions.append(
            "EXISTS (SELECT 1 FROM jsonb_object_keys(codified_data) AS k WHERE lower(k) = lower(%(term)s))"
        )
        conditions.append(
            "EXISTS (SELECT 1 FROM jsonb_each(codified_data) AS kv"
            " WHERE lower(kv.key) = lower(%(term)s)"
            " AND EXISTS (SELECT 1 FROM jsonb_object_keys(kv.value) AS k2 WHERE lower(k2) = lower(%(attribute)s)))"
        )
        params["term"] = term
        params["attribute"] = attribute
    elif term:
        conditions.append(
            "EXISTS (SELECT 1 FROM jsonb_object_keys(codified_data) AS k WHERE lower(k) = lower(%(term)s))"
        )
        params["term"] = term
    elif attribute:
        conditions.append(
            "EXISTS (SELECT 1 FROM jsonb_each(codified_data) AS kv"
            " WHERE EXISTS (SELECT 1 FROM jsonb_object_keys(kv.value) AS k2 WHERE lower(k2) = lower(%(attribute)s)))"
        )
        params["attribute"] = attribute

    where_clause = " AND ".join(conditions)

    if embedding:
        vector_literal = to_pgvector_literal(embedding)
        params["vector"] = vector_literal
        query = f"""
            SELECT
                id, client_id, text_content, codified_data,
                query_history, doc_count, last_updated,
                1 - (embedding <=> %(vector)s::vector) AS relevance_score
            FROM clusters
            WHERE {where_clause}
            ORDER BY embedding <=> %(vector)s::vector
            LIMIT %(top_k)s
        """
    else:
        query = f"""
            SELECT
                id, client_id, text_content, codified_data,
                query_history, doc_count, last_updated,
                1.0 AS relevance_score
            FROM clusters
            WHERE {where_clause}
            ORDER BY last_updated DESC NULLS LAST
            LIMIT %(top_k)s
        """

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(query, params)
        return list(cur.fetchall())


def search_clusters_structured_across_clients(
    conn,
    client_ids: list[str],
    top_k: int,
    term: str | None = None,
    attribute: str | None = None,
    embedding: list[float] | None = None,
) -> list[dict]:
    combined: list[dict] = []
    for client_id in client_ids:
        combined.extend(
            search_clusters_structured(conn, client_id, top_k, term, attribute, embedding)
        )

    combined.sort(key=lambda row: float(row["relevance_score"]), reverse=True)
    return combined[:top_k]
