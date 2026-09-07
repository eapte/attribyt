import json
import sqlite3
from pathlib import Path
from typing import List, Optional
from .models import Source

# SQLite file lives under /app/data, which is mounted as a Docker volume
# (see docker-compose.yml) so data survives image rebuilds and restarts.
DB_PATH = Path(__file__).parent.parent / "data" / "attribyt.db"


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    conn = _get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            credentials TEXT NOT NULL,
            sync_mode TEXT NOT NULL,
            cursor TEXT,
            last_sync TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            last_error TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS synced_rows (
            source_id TEXT NOT NULL,
            row_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


class SourceService:
    """Handles reading and writing Source records, backed by SQLite."""

    def __init__(self):
        _init_db()

    def _row_to_source(self, row: sqlite3.Row) -> Source:
        return Source.from_dict(
            {
                "id": row["id"],
                "type": row["type"],
                "name": row["name"],
                "credentials": json.loads(row["credentials"]),
                "sync_mode": row["sync_mode"],
                "cursor": row["cursor"],
                "last_sync": row["last_sync"],
                "created_at": row["created_at"],
                "status": row["status"],
                "last_error": row["last_error"],
            }
        )

    def list_sources(self) -> List[Source]:
        conn = _get_connection()
        rows = conn.execute("SELECT * FROM sources ORDER BY created_at DESC").fetchall()
        conn.close()
        return [self._row_to_source(r) for r in rows]

    def get_source(self, source_id: str) -> Optional[Source]:
        conn = _get_connection()
        row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
        conn.close()
        return self._row_to_source(row) if row else None

    def create_source(self, source: Source) -> Source:
        d = source.to_dict()
        conn = _get_connection()
        conn.execute(
            """
            INSERT INTO sources (id, type, name, credentials, sync_mode, cursor, last_sync, created_at, status, last_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                d["id"],
                d["type"],
                d["name"],
                json.dumps(d["credentials"]),
                d["sync_mode"],
                d["cursor"],
                d["last_sync"],
                d["created_at"],
                d["status"],
                d["last_error"],
            ),
        )
        conn.commit()
        conn.close()
        return source

    def delete_source(self, source_id: str) -> bool:
        conn = _get_connection()
        cursor = conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        conn.execute("DELETE FROM synced_rows WHERE source_id = ?", (source_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def update_status(self, source_id: str, status: str) -> Optional[Source]:
        conn = _get_connection()
        conn.execute("UPDATE sources SET status = ? WHERE id = ?", (status, source_id))
        conn.commit()
        conn.close()
        return self.get_source(source_id)

    def save_synced_rows(self, source_id: str, rows: list[dict]) -> None:
        conn = _get_connection()
        conn.execute("DELETE FROM synced_rows WHERE source_id = ?", (source_id,))
        conn.executemany(
            "INSERT INTO synced_rows (source_id, row_json) VALUES (?, ?)",
            [(source_id, json.dumps(r, default=str)) for r in rows],
        )
        conn.commit()
        conn.close()

    def get_synced_rows(self, source_id: str) -> list[dict]:
        conn = _get_connection()
        rows = conn.execute("SELECT row_json FROM synced_rows WHERE source_id = ?", (source_id,)).fetchall()
        conn.close()
        return [json.loads(r["row_json"]) for r in rows]

    def update_last_sync(self, source_id: str, last_sync: str) -> None:
        conn = _get_connection()
        conn.execute("UPDATE sources SET last_sync = ? WHERE id = ?", (last_sync, source_id))
        conn.commit()
        conn.close()

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        """Returns a simple activity feed based on real source events —
        currently just successful/failed syncs, ordered by last_sync desc.
        Not a general event log yet, just what we can honestly report."""
        conn = _get_connection()
        rows = conn.execute(
            """
            SELECT name, type, status, last_error, last_sync
            FROM sources
            WHERE last_sync IS NOT NULL
            ORDER BY last_sync DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows] 