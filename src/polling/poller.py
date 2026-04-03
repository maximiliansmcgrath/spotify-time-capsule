"""
Poll Spotify's recently-played endpoint and store new listens in SQLite.

The API returns up to 50 recent tracks. We track the last poll timestamp
so we only insert new plays each time.
"""

import time
from datetime import datetime

from rich.console import Console

from src.auth.spotify_auth import get_spotify_client
from src.ingestion.database import get_connection, init_db

console = Console()

INSERT_SQL = """
INSERT OR IGNORE INTO streams (
    ts, track_name, artist_name, album_name, spotify_track_uri, ms_played,
    preview_url, album_image_url
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


def _fetch_recent_plays(sp, after_ms: int | None = None) -> list[dict]:
    """Fetch recently played tracks from Spotify API.

    Args:
        sp: Authenticated Spotify client.
        after_ms: Unix timestamp in ms — only return plays after this time.
    """
    kwargs = {"limit": 50}
    if after_ms:
        kwargs["after"] = after_ms
    results = sp.current_user_recently_played(**kwargs)
    return results.get("items", [])


def _parse_play(item: dict) -> tuple:
    """Parse a single play item from the API into a DB row."""
    track = item["track"]
    played_at = item["played_at"]  # ISO 8601 UTC string
    # Get the largest album image (first in the list, usually 640px)
    images = track.get("album", {}).get("images", [])
    album_image_url = images[0]["url"] if images else None
    return (
        played_at,
        track["name"],
        ", ".join(a["name"] for a in track["artists"]),
        track["album"]["name"],
        track["uri"],
        track["duration_ms"],
        track.get("preview_url"),
        album_image_url,
    )


def _played_at_to_ms(played_at: str) -> int:
    """Convert an ISO 8601 timestamp to Unix ms for the 'after' cursor."""
    dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def poll_once() -> dict:
    """Run a single poll: fetch recent plays and store new ones.

    Returns a summary dict with fetched and new_records counts.
    """
    init_db()
    sp = get_spotify_client()
    conn = get_connection()

    # Get the most recent timestamp we have from API-sourced data.
    row = conn.execute(
        "SELECT MAX(ts) as last_ts FROM streams"
    ).fetchone()
    last_ts = row["last_ts"] if row else None
    after_ms = _played_at_to_ms(last_ts) if last_ts else None

    items = _fetch_recent_plays(sp, after_ms)
    rows = [_parse_play(item) for item in items]

    cursor = conn.executemany(INSERT_SQL, rows)
    new_count = cursor.rowcount
    conn.commit()
    conn.close()

    return {"fetched": len(items), "new_records": new_count}


def poll_continuous(interval_minutes: int = 5) -> None:
    """Continuously poll for new plays at a regular interval.

    Args:
        interval_minutes: Minutes between each poll.
    """
    init_db()
    sp = get_spotify_client()
    interval_sec = interval_minutes * 60

    console.print(f"Polling every [bold]{interval_minutes} minutes[/bold]. Press Ctrl+C to stop.\n")

    poll_count = 0
    total_new = 0

    try:
        while True:
            conn = get_connection()

            row = conn.execute("SELECT MAX(ts) as last_ts FROM streams").fetchone()
            last_ts = row["last_ts"] if row else None
            after_ms = _played_at_to_ms(last_ts) if last_ts else None

            items = _fetch_recent_plays(sp, after_ms)
            rows = [_parse_play(item) for item in items]

            cursor = conn.executemany(INSERT_SQL, rows)
            new_count = cursor.rowcount
            conn.commit()
            conn.close()

            poll_count += 1
            total_new += new_count
            now = datetime.now().strftime("%H:%M:%S")

            if new_count > 0:
                console.print(
                    f"[dim]{now}[/dim]  Poll #{poll_count}: "
                    f"[green]+{new_count} new[/green] track(s) saved"
                )
                # Show what was just added
                for row in rows[:new_count]:
                    console.print(f"         [cyan]{row[1]}[/cyan] — {row[2]}")
            else:
                console.print(
                    f"[dim]{now}[/dim]  Poll #{poll_count}: no new tracks"
                )

            time.sleep(interval_sec)

    except KeyboardInterrupt:
        console.print(f"\n Stopped. {poll_count} polls, {total_new} new tracks saved total.")
