"""
Rich terminal display for flashback results.
Handles album art display and Spotify playback.
"""

import io
from datetime import datetime

import requests
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.flashback.engine import Flashback

console = Console()


def _format_duration(ms: int) -> str:
    """Format milliseconds as a human-readable duration."""
    seconds = ms // 1000
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    remaining_min = minutes % 60
    return f"{hours}h {remaining_min}m"


def _years_ago_label(n: int) -> str:
    if n == 0:
        return "This year"
    if n == 1:
        return "1 year ago"
    return f"{n} years ago"


def _display_album_art(url: str) -> None:
    """Download and display album art in the terminal using Unicode blocks."""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        # Terminal chars are ~2x tall as wide. Each "▀" half-block packs
        # 2 pixel rows into 1 terminal row. For a square image we need
        # cols terminal chars wide × cols terminal rows tall,
        # which means cols pixel-cols × (cols * 2) pixel-rows.
        # But since each char is ~2x tall as wide, cols chars wide =
        # cols rows tall visually. So pixel dimensions: cols × cols.
        cols = min(console.width, 120)
        rows = cols  # square: half-blocks make this render as square
        img = img.resize((cols, rows)).convert("RGB")
        pixels = img.load()

        for y in range(0, rows, 2):
            line = ""
            for x in range(cols):
                # Top pixel → foreground, bottom pixel → background
                tr, tg, tb = pixels[x, y]
                br, bg, bb = pixels[x, y + 1]
                line += f"\033[38;2;{tr};{tg};{tb};48;2;{br};{bg};{bb}m\u2580"
            line += "\033[0m"
            print(line)
    except Exception:
        pass  # Silently skip if art can't be displayed


def _play_on_spotify(track_uri: str, sp) -> None:
    """Start playing a track on the user's active Spotify device."""
    try:
        sp.start_playback(uris=[track_uri])
    except Exception:
        pass  # No active device, not premium, etc.


def _no_memories_panel(message: str) -> None:
    console.print(
        Panel(
            f"[dim]{message}[/dim]\n"
            "Poll some tracks or import your history first.",
            title="No Memories Yet",
            border_style="dim",
        )
    )


def display_flashback(fb: Flashback | None, title: str = "Your Musical Memory") -> None:
    """Render a single-track flashback with album art and Spotify playback."""
    if not fb:
        _no_memories_panel("No musical memories found for this date.")
        return

    track = fb.track

    # Start playback on Spotify
    if track.spotify_track_uri:
        from src.auth.spotify_auth import get_spotify_client
        sp = get_spotify_client()
        _play_on_spotify(track.spotify_track_uri, sp)

    console.print()
    console.print(Text(title, style="bold magenta", justify="center"))
    console.print()

    # Album art
    if track.album_image_url:
        _display_album_art(track.album_image_url)
        console.print()

    # Track info
    time_str = ""
    if track.played_at:
        try:
            dt = datetime.fromisoformat(track.played_at.replace("Z", "+00:00"))
            local_dt = dt.astimezone()
            time_str = f"  \u2022  {local_dt.strftime('%-I:%M %p')}"
        except ValueError:
            pass

    header = (
        f"{_years_ago_label(fb.years_ago)}  \u2022  "
        f"{fb.date.strftime('%B %d, %Y')}{time_str}"
    )

    info_lines = Text()
    info_lines.append(track.track_name or "Unknown", style="bold white")
    info_lines.append("\n")
    info_lines.append(track.artist_name or "Unknown", style="cyan")
    if track.album_name:
        info_lines.append("\n")
        info_lines.append(track.album_name, style="dim")
    info_lines.append("\n")
    info_lines.append(
        f"Played {track.play_count}x \u2022 {_format_duration(track.total_ms_played)} total",
        style="dim",
    )
    if track.spotify_track_uri:
        info_lines.append("\n")
        info_lines.append("Now playing on Spotify", style="green italic")

    console.print(
        Panel(
            info_lines,
            title=header,
            border_style="magenta",
            padding=(1, 2),
        )
    )
    console.print()
