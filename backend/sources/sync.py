import sqlite3
import requests
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
        return _sync_sqlite(query)

    raise SyncError(f"The '{driver}' driver isn't implemented yet — only SQLite is functional so far.")


def _sync_sqlite(query: str) -> List[Dict]:
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


def sync_rest_api(credentials: dict) -> List[Dict]:
    """Fetches JSON from the configured URL and returns the rows as-is.
    Accepts either a top-level JSON array, or an object with a 'data' key
    holding the array. Does NOT assume any particular column names —
    whatever the API returns is stored verbatim; analysis will report
    clearly if the expected columns aren't present."""
    url = credentials.get("url", "").strip()
    if not url:
        raise SyncError("No URL configured for this source.")

    headers = {}
    token = credentials.get("token", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
    except requests.exceptions.RequestException as e:
        raise SyncError(f"Request failed: {e}")
    except ValueError:
        raise SyncError("Response wasn't valid JSON.")

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = payload["data"]
    else:
        raise SyncError("Expected a JSON array (or an object with a 'data' array) in the response.")

    if not all(isinstance(r, dict) for r in rows):
        raise SyncError("Expected each item in the response array to be an object.")

    return rows 