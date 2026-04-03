"""
SQLite database setup and connection management for Spotify Time Capsule.
Stores listening history with full metadata from Spotify's extended export.
"""

import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "listening_history.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    track_name TEXT,
    artist_name TEXT,
    album_name TEXT,
    spotify_track_uri TEXT,
    ms_played INTEGER NOT NULL,
    reason_start TEXT,
    reason_end TEXT,
    shuffle INTEGER,
    skipped INTEGER,
    platform TEXT,
    conn_country TEXT,
    ip_addr TEXT,
    episode_name TEXT,
    episode_show_name TEXT,
    spotify_episode_uri TEXT,
    offline INTEGER,
    offline_timestamp INTEGER,
    incognito_mode INTEGER,
    preview_url TEXT,
    album_image_url TEXT,
    UNIQUE(ts, spotify_track_uri, ms_played)
);

CREATE INDEX IF NOT EXISTS idx_streams_ts ON streams(ts);
CREATE INDEX IF NOT EXISTS idx_streams_track_uri ON streams(spotify_track_uri);
CREATE INDEX IF NOT EXISTS idx_streams_artist ON streams(artist_name);
CREATE INDEX IF NOT EXISTS idx_streams_date ON streams(substr(ts, 1, 10));
"""


def get_connection() -> sqlite3.Connection:
    """Get a connection to the listening history database."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


MIGRATIONS = [
    "ALTER TABLE streams ADD COLUMN preview_url TEXT",
    "ALTER TABLE streams ADD COLUMN album_image_url TEXT",
]


def init_db() -> None:
    """Create the database schema and run any pending migrations."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    for migration in MIGRATIONS:
        try:
            conn.execute(migration)
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()
    conn.close()
