import psycopg2
import psycopg2.extras
from contextlib import contextmanager

DB_CONFIG = {
    'dbname': 'kasir_db',
    'user': 'postgres',
    'password': '5432',
    'host': 'localhost',
    'port': 5432
}

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_db_cursor(commit=False):
    """
    Legacy wrapper kept for compatibility with other modules if needed,
    but services.py will use get_db_connection directly.
    """
    with get_db_connection() as conn:
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
