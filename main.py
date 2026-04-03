"""
Spotify Time Capsule - CLI entry point.
"""

from datetime import date, datetime
from pathlib import Path

import click
from rich.console import Console

from src.auth.spotify_auth import test_connection
from src.flashback.display import display_flashback
from src.flashback.engine import get_flashback, get_random_flashback
from src.ingestion.ingest import ingest_files
from src.polling.poller import poll_once, poll_continuous

console = Console()


@click.group()
def cli():
    """🎵 Spotify Time Capsule — your musical memories."""
    pass


@cli.command()
def connect():
    """Test your Spotify API connection."""
    console.print("[bold]🎵 Spotify Time Capsule[/bold]")
    console.print("=" * 40)
    console.print("\nTesting Spotify connection...\n")

    success = test_connection()

    if success:
        console.print("\n[green]🎉 You're all set! Your credentials are working.[/green]")
        console.print("   Next step: Request your extended listening history from")
        console.print("   Spotify (Account → Privacy → Request Data)")
    else:
        console.print("\n[yellow]💡 Troubleshooting:[/yellow]")
        console.print("   1. Check that your .env file has the correct credentials")
        console.print("   2. Make sure http://127.0.0.1:8888/callback is in your")
        console.print("      Spotify app's redirect URIs")
        console.print("   3. Try regenerating your Client Secret if it's not working")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, path_type=Path))
def ingest(directory: Path):
    """Import Spotify extended streaming history export.

    DIRECTORY is the path to the folder containing your
    Streaming_History_Audio_*.json files.
    """
    console.print("[bold]🎵 Spotify Time Capsule — Data Import[/bold]\n")
    ingest_files(directory)


@cli.command()
@click.option(
    "--date", "-d", "target_date", default=None,
    help="Date to look up (YYYY-MM-DD). Defaults to today.",
)
@click.option(
    "--window", "-w", default=0, show_default=True,
    help="Expand search +/- this many days around the target date.",
)
def flashback(target_date: str | None, window: int):
    """Show what you were listening to on this day in past years."""
    console.print("[bold]🎵 Spotify Time Capsule — Flashback[/bold]\n")

    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        dt = date.today()

    label = dt.strftime("%B %d")
    if window > 0:
        console.print(f"Looking up memories around [bold]{label}[/bold] (+/- {window} days)...\n")
    else:
        console.print(f"Looking up memories for [bold]{label}[/bold]...\n")

    fb = get_flashback(target_date=dt, window_days=window)
    display_flashback(fb, title="On This Day")


@cli.command(name="random")
def random_flashback():
    """Show a random musical memory from any date in your history."""
    console.print("[bold]🎵 Spotify Time Capsule — Random Memory[/bold]\n")
    fb = get_random_flashback()
    display_flashback(fb, title="Random Musical Memory")


@cli.command()
@click.option(
    "--interval", "-i", default=5, show_default=True,
    help="Minutes between polls (0 = poll once and exit).",
)
def poll(interval: int):
    """Collect your recent Spotify plays into the database."""
    console.print("[bold]🎵 Spotify Time Capsule — Live Polling[/bold]\n")

    if interval == 0:
        summary = poll_once()
        if summary["new_records"]:
            console.print(
                f"[green]+{summary['new_records']} new[/green] track(s) saved "
                f"(fetched {summary['fetched']} from API)"
            )
        else:
            console.print(f"No new tracks (fetched {summary['fetched']} from API)")
    else:
        poll_continuous(interval_minutes=interval)


if __name__ == "__main__":
    cli()
