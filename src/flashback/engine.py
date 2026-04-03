"""
Flashback engine — musical memory lookups.

Two modes:
  - "On this day": what you listened to on this calendar date in past years.
  - "Random": pick a random date from your entire history.
"""

import random
from dataclasses import dataclass
from datetime import date, timedelta

from src.ingestion.database import get_connection, init_db

# Minimum ms_played to count as a real listen (30 seconds).
MIN_MS_PLAYED = 30_000


@dataclass
class TrackMemory:
    """A single track from a past listening session."""
    track_name: str
    artist_name: str
    album_name: str | None
    play_count: int
    total_ms_played: int
    spotify_track_uri: str | None
    preview_url: str | None
    album_image_url: str | None
    played_at: str | None


@dataclass
class Flashback:
    """A single musical memory — one track from a past date."""
    date: date
    years_ago: int
    track: TrackMemory


def get_flashback(
    target_date: date | None = None,
    window_days: int = 0,
    min_ms: int = MIN_MS_PLAYED,
) -> Flashback | None:
    """Find a single top-track memory for this calendar date from a past year.

    Picks the most recent past year that has data, and returns the
    top track from that date. Skips the current year.
    """
    init_db()
    if target_date is None:
        target_date = date.today()

    conn = get_connection()
    years = _find_years_with_data(conn, target_date, window_days, min_ms)

    for year in years:
        if year == target_date.year:
            continue
        track = _get_top_track_for_year(conn, target_date, year, window_days, min_ms)
        if track:
            conn.close()
            past_date = target_date.replace(year=year)
            return Flashback(
                date=past_date,
                years_ago=target_date.year - year,
                track=track,
            )

    conn.close()
    return None



def _date_patterns(target_date: date, window_days: int) -> list[str]:
    """Generate MM-DD patterns for the target date +/- window."""
    patterns = []
    for offset in range(-window_days, window_days + 1):
        d = target_date + timedelta(days=offset)
        patterns.append(d.strftime("%m-%d"))
    return patterns


def _find_years_with_data(
    conn, target_date: date, window_days: int, min_ms: int
) -> list[int]:
    """Find all years that have listening data for the given MM-DD pattern(s)."""
    patterns = _date_patterns(target_date, window_days)
    placeholders = ",".join("?" for _ in patterns)

    rows = conn.execute(
        f"""
        SELECT DISTINCT CAST(substr(ts, 1, 4) AS INTEGER) as year
        FROM streams
        WHERE substr(ts, 6, 5) IN ({placeholders})
          AND ms_played >= ?
        ORDER BY year DESC
        """,
        [*patterns, min_ms],
    ).fetchall()

    return [r["year"] for r in rows]


def _get_top_track_for_year(
    conn,
    target_date: date,
    year: int,
    window_days: int,
    min_ms: int,
) -> TrackMemory | None:
    """Get the single top track for a specific year on this calendar date."""
    patterns = _date_patterns(target_date, window_days)
    placeholders = ",".join("?" for _ in patterns)

    row = conn.execute(
        f"""
        SELECT
            track_name,
            artist_name,
            album_name,
            spotify_track_uri,
            preview_url,
            album_image_url,
            MIN(ts) as first_played_at,
            COUNT(*) as play_count,
            SUM(ms_played) as total_ms_played
        FROM streams
        WHERE CAST(substr(ts, 1, 4) AS INTEGER) = ?
          AND substr(ts, 6, 5) IN ({placeholders})
          AND ms_played >= ?
          AND track_name IS NOT NULL
        GROUP BY track_name, artist_name
        ORDER BY play_count DESC, total_ms_played DESC
        LIMIT 1
        """,
        [year, *patterns, min_ms],
    ).fetchone()

    if not row:
        return None

    return TrackMemory(
        track_name=row["track_name"],
        artist_name=row["artist_name"],
        album_name=row["album_name"],
        play_count=row["play_count"],
        total_ms_played=row["total_ms_played"],
        spotify_track_uri=row["spotify_track_uri"],
        preview_url=row["preview_url"],
        album_image_url=row["album_image_url"],
        played_at=row["first_played_at"],
    )


def get_random_flashback(
    min_ms: int = MIN_MS_PLAYED,
) -> Flashback | None:
    """Pick a random track from your entire listening history.

    Unlike get_flashback, this includes the current year.
    """
    init_db()
    conn = get_connection()

    # Pick a single random play — no grouping, so the timestamp is exact.
    row = conn.execute(
        """
        SELECT
            ts,
            substr(ts, 1, 10) as listen_date,
            track_name,
            artist_name,
            album_name,
            spotify_track_uri,
            preview_url,
            album_image_url,
            ms_played
        FROM streams
        WHERE ms_played >= ?
          AND track_name IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1
        """,
        [min_ms],
    ).fetchone()

    conn.close()

    if not row:
        return None

    chosen_date = date.fromisoformat(row["listen_date"])
    today = date.today()
    years_ago = today.year - chosen_date.year
    if (today.month, today.day) < (chosen_date.month, chosen_date.day):
        years_ago -= 1

    track = TrackMemory(
        track_name=row["track_name"],
        artist_name=row["artist_name"],
        album_name=row["album_name"],
        play_count=1,
        total_ms_played=row["ms_played"],
        spotify_track_uri=row["spotify_track_uri"],
        preview_url=row["preview_url"],
        album_image_url=row["album_image_url"],
        played_at=row["ts"],
    )

    return Flashback(
        date=chosen_date,
        years_ago=max(years_ago, 0),
        track=track,
    )
