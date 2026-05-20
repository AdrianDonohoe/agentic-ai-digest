"""SQLite-backed seen-URL state."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "seen.db"


def init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_urls (
            url  TEXT PRIMARY KEY,
            title TEXT,
            seen_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def is_seen(conn: sqlite3.Connection, url: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM seen_urls WHERE url = ?", (url,)
    ).fetchone() is not None


def mark_seen(conn: sqlite3.Connection, url: str, title: str = "") -> None:
    conn.execute(
        "INSERT OR IGNORE INTO seen_urls (url, title) VALUES (?, ?)",
        (url, title),
    )
