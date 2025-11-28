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

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

@contextmanager
def get_db_cursor(commit=False):
    conn = get_db_connection()
    try:
        # Use RealDictCursor to access columns by name
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
