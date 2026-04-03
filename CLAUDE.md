# Spotify Time Capsule

## What This Project Is
A Python CLI tool that creates "musical memories" — flashbacks showing what you were listening to on this day 1, 2, 3+ years ago, similar to Snapchat Memories but for your Spotify listening history.

## Tech Stack
- **Language:** Python 3.10+
- **Spotify API:** via `spotipy` library
- **Database:** SQLite (for storing listening history)
- **CLI framework:** `click` + `rich` for terminal UI
- **Auth:** OAuth 2.0 Authorization Code flow

## Project Structure
```
spotify-time-capsule/
├── main.py                        # CLI entry point (click commands)
├── src/
│   ├── auth/
│   │   ├── config.py              # .env credential loader
│   │   └── spotify_auth.py        # OAuth flow + Spotify client
│   ├── ingestion/
│   │   ├── database.py            # SQLite schema, connection, migrations
│   │   └── ingest.py              # JSON export parser (basic + extended)
│   ├── flashback/
│   │   ├── engine.py              # "On this day" + random memory queries
│   │   └── display.py             # Rich terminal UI, album art, Spotify playback
│   └── polling/
│       └── poller.py              # Recently-played API poller
├── config/
│   └── .env                       # Spotify API credentials (gitignored)
├── data/                          # SQLite DB (gitignored)
└── requirements.txt
```

## Key Decisions
- Secrets stored in `.env` file, loaded via `python-dotenv`. NEVER hardcode credentials.
- `.spotify_cache` stores OAuth tokens locally (also gitignored).
- Historical data comes from Spotify's data export (JSON). Supports both basic (`StreamingHistory_music_*.json`) and extended (`Streaming_History_Audio_*.json`) formats.
- Real-time data from the recently-played API endpoint (max 50 tracks per poll).
- All dates stored in UTC in the database, converted to local timezone for display.
- Spotify preview URLs are deprecated; playback uses Spotify Connect API instead (requires Premium).
- Album art rendered in terminal using half-block Unicode characters (`▀`) with true-color ANSI escapes.

## Conventions
- Use type hints on all function signatures.
- Docstrings on all public functions.
- Keep modules focused — one responsibility per file.
- Use `rich` for any terminal output formatting.

## How to Run
1. Copy `config/.env.example` to `config/.env` and add your Spotify API credentials.
2. `pip install -r requirements.txt`
3. `python main.py connect` — test your credentials.
4. `python main.py poll -i 0` — pull your last 50 plays.
5. `python main.py random` — show a random memory with album art + playback.
6. `python main.py flashback` — show "on this day" from past years.
7. `python main.py ingest /path/to/export` — import a Spotify data export.

## Current Status
- [x] Project scaffolding
- [x] Secure credential loading
- [x] Spotify OAuth flow
- [x] Data export ingestion (basic + extended formats)
- [x] SQLite schema + storage (with migrations)
- [x] Flashback engine ("on this day" + random)
- [x] Polling service (single + continuous)
- [x] Rich CLI output with album art + Spotify Connect playback
- [ ] Web UI (planned: React + FastAPI, Figma-driven design)
