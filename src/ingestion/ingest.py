"""
Ingest Spotify streaming history JSON exports into SQLite.

Supports both export formats:
  - Basic:    StreamingHistory_music_*.json  (endTime, trackName, artistName, msPlayed)
  - Extended: Streaming_History_Audio_*.json (ts, master_metadata_*, ms_played, ...)
"""

import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from src.ingestion.database import get_connection, init_db

console = Console()

# Maps extended export field names to our database column names.
EXTENDED_FIELD_MAP = {
    "ts": "ts",
    "master_metadata_track_name": "track_name",
    "master_metadata_album_artist_name": "artist_name",
    "master_metadata_album_album_name": "album_name",
    "spotify_track_uri": "spotify_track_uri",
    "ms_played": "ms_played",
    "reason_start": "reason_start",
    "reason_end": "reason_end",
    "shuffle": "shuffle",
    "skipped": "skipped",
    "platform": "platform",
    "conn_country": "conn_country",
    "ip_addr_decrypted": "ip_addr",
    "episode_name": "episode_name",
    "episode_show_name": "episode_show_name",
    "spotify_episode_uri": "spotify_episode_uri",
    "offline": "offline",
    "offline_timestamp": "offline_timestamp",
    "incognito_mode": "incognito_mode",
}

# All DB columns (used to fill missing fields with None).
ALL_COLUMNS = list(EXTENDED_FIELD_MAP.values())

INSERT_SQL = """
INSERT OR IGNORE INTO streams (
    ts, track_name, artist_name, album_name, spotify_track_uri,
    ms_played, reason_start, reason_end, shuffle, skipped,
    platform, conn_country, ip_addr, episode_name, episode_show_name,
    spotify_episode_uri, offline, offline_timestamp, incognito_mode
) VALUES (
    :ts, :track_name, :artist_name, :album_name, :spotify_track_uri,
    :ms_played, :reason_start, :reason_end, :shuffle, :skipped,
    :platform, :conn_country, :ip_addr, :episode_name, :episode_show_name,
    :spotify_episode_uri, :offline, :offline_timestamp, :incognito_mode
)
"""


def _map_basic_record(raw: dict) -> dict:
    """Map a basic export record to our DB column names.

    Basic format has: endTime, artistName, trackName, msPlayed.
    endTime is like "2023-01-15 14:30" — we normalize to ISO 8601 UTC.
    """
    row = {col: None for col in ALL_COLUMNS}
    end_time = raw.get("endTime", "")
    row["ts"] = end_time.replace(" ", "T") + "Z" if end_time else None
    row["track_name"] = raw.get("trackName")
    row["artist_name"] = raw.get("artistName")
    row["ms_played"] = raw.get("msPlayed")
    return row


def _map_extended_record(raw: dict) -> dict:
    """Map an extended export record to our DB column names."""
    return {db_col: raw.get(export_key) for export_key, db_col in EXTENDED_FIELD_MAP.items()}


def _detect_format(records: list[dict]) -> str:
    """Detect whether records are from basic or extended export."""
    if not records:
        return "extended"
    first = records[0]
    if "endTime" in first:
        return "basic"
    return "extended"


def find_export_files(directory: Path) -> list[Path]:
    """Find all Spotify streaming history JSON files in a directory."""
    # Extended format
    files = sorted(directory.glob("Streaming_History_Audio_*.json"))
    # Basic format
    files += sorted(directory.glob("StreamingHistory_music_*.json"))
    files += sorted(directory.glob("StreamingHistory*.json"))
    # Deduplicate (in case glob patterns overlap) while preserving order
    seen = set()
    unique = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def ingest_files(directory: Path) -> dict:
    """Ingest all Spotify export JSON files from a directory.

    Returns a summary dict with total_files, total_records, new_records.
    """
    init_db()
    export_files = find_export_files(directory)

    if not export_files:
        console.print(
            f"[red]No Spotify export files found in {directory}[/red]\n"
            "Expected files matching: Streaming_History_Audio_*.json (extended)\n"
            "  or StreamingHistory_music_*.json (basic)"
        )
        return {"total_files": 0, "total_records": 0, "new_records": 0}

    console.print(f"Found [bold]{len(export_files)}[/bold] export file(s)\n")

    conn = get_connection()
    total_records = 0
    new_records = 0

    for filepath in export_files:
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)

        fmt = _detect_format(records)
        mapper = _map_basic_record if fmt == "basic" else _map_extended_record
        mapped = [mapper(r) for r in records]
        cursor = conn.executemany(INSERT_SQL, mapped)
        file_new = cursor.rowcount
        new_records += file_new
        total_records += len(records)

        fmt_label = f"[cyan]{fmt}[/cyan]"
        status = f"[green]+{file_new} new[/green]" if file_new else "[dim]no new[/dim]"
        console.print(f"  {filepath.name} ({fmt_label}): {len(records)} records ({status})")

    conn.commit()
    conn.close()

    summary = {
        "total_files": len(export_files),
        "total_records": total_records,
        "new_records": new_records,
    }
    _print_summary(summary)
    return summary


def _print_summary(summary: dict) -> None:
    """Print a rich summary table after ingestion."""
    console.print()
    table = Table(title="Ingestion Summary")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Files processed", str(summary["total_files"]))
    table.add_row("Total records", str(summary["total_records"]))
    table.add_row("New records added", str(summary["new_records"]))
    table.add_row(
        "Duplicates skipped",
        str(summary["total_records"] - summary["new_records"]),
    )
    console.print(table)
