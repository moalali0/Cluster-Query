from contextlib import contextmanager

from psycopg_pool import ConnectionPool

from .config import settings


def _check_conn(conn):
    conn.execute("SELECT 1")


app_pool = ConnectionPool(
    conninfo=settings.app_database_url,
    min_size=1,
    max_size=10,
    timeout=30,
    check=_check_conn,
    max_idle=300,
)
ingest_pool = ConnectionPool(
    conninfo=settings.ingest_database_url,
    min_size=1,
    max_size=4,
    timeout=30,
    check=_check_conn,
    max_idle=300,
)


@contextmanager
def get_app_conn():
    with app_pool.connection() as conn:
        yield conn


@contextmanager
def get_ingest_conn():
    with ingest_pool.connection() as conn:
        yield conn
