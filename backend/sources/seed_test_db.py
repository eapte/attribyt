import sqlite3
from pathlib import Path

# This simulates an external database a user might connect to —
# separate from attribyt's own data/attribyt.db which stores source configs.
TEST_DB_PATH = Path(__file__).parent.parent / "data" / "test_shop.db"

SAMPLE_ORDERS = [
    ("user_1", "2026-01-01 10:00:00", "google_ads", 45.00),
    ("user_1", "2026-01-02 14:30:00", "direct", 120.00),
    ("user_2", "2026-01-01 09:15:00", "email", 30.00),
    ("user_2", "2026-01-03 11:00:00", "organic", 89.50),
    ("user_3", "2026-01-01 16:45:00", "facebook_ads", 65.00),
    ("user_3", "2026-01-02 08:20:00", "facebook_ads", 65.00),
    ("user_3", "2026-01-04 13:10:00", "direct", 210.00),
    ("user_4", "2026-01-01 12:00:00", "telegram", 40.00),
    ("user_5", "2026-01-02 17:30:00", "google_ads", 95.00),
    ("user_5", "2026-01-03 10:45:00", "organic", 55.00),
]


def seed_test_db() -> None:
    """Creates a sample 'external' SQLite database with an orders table,
    so Database sources can be tested end-to-end without setting up a
    real Postgres/MySQL server."""
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            channel TEXT NOT NULL,
            revenue REAL NOT NULL
        )
        """
    )
    existing = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if existing == 0:
        conn.executemany(
            "INSERT INTO orders (user_id, timestamp, channel, revenue) VALUES (?, ?, ?, ?)",
            SAMPLE_ORDERS,
        )
        conn.commit()
    conn.close() 