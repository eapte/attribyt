import sqlite3
from pathlib import Path
from typing import List, Dict

from .seed_test_db import TEST_DB_PATH


class SyncError(Exception):
    pass


def sync_database(credentials: dict) -> List[Dict]:
    """Runs the configured query against the source and returns normalized rows.
    Only the 'sqlite' driver is functional right now — postgres/mysql are
    accepted in the form but not yet implemented."""
    driver = credentials.get("driver", "sqlite")
    query = credentials.get("query", "").strip()

    if not query:
        raise SyncError("No query configured for this source.")

    if driver == "sqlite":
        return _sync_sqlite(credentials, query)

    raise SyncError(f"The '{driver}' driver isn't implemented yet — only SQLite is functional so far.")


def _sync_sqlite(credentials: dict, query: str) -> List[Dict]:
    # For the test driver we always point at the seeded sample database,
    # ignoring any file_path the user might type — this is a sandbox for
    # trying out the sync mechanism, not a general file browser.
    if not TEST_DB_PATH.exists():
        raise SyncError("Test database not found — it should be seeded on backend startup.")

    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error as e:
        raise SyncError(f"Query failed: {e}")
    finally:
        conn.close()

    return [dict(row) for row in rows] 