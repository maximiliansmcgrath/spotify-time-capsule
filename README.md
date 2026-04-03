# Spotify Time Capsule

**"On This Day" musical memories — see what you were listening to 1, 2, 3+ years ago.**

Like Snapchat Memories, but for your Spotify listening history. Get a daily flashback to the songs that defined your past.

## Features

- **On This Day** — See what you were playing on today's date in previous years
- **Random Flashback** — Jump to a random day in your listening history
- **Mood Analysis** — See how your music taste has evolved over time
- **Auto-Collection** — Continuously logs your listening for future memories

## Quick Start

### 1. Get Spotify API Credentials
- Go to [developer.spotify.com](https://developer.spotify.com/dashboard)
- Create a new app
- Add `http://127.0.0.1:8888/callback` as a Redirect URI

### 2. Set Up the Project
```bash
git clone https://github.com/YOUR_USERNAME/spotify-time-capsule.git
cd spotify-time-capsule
pip install -r requirements.txt
```

### 3. Add Your Credentials
```bash
cp config/.env.example config/.env
# Edit config/.env with your Client ID and Client Secret
```

### 4. Test Your Connection
```bash
python main.py
```

### 5. (Optional) Import Your Full History
Request your extended streaming history from [Spotify Account Privacy Settings](https://www.spotify.com/account/privacy/). Place the JSON files in the `data/` directory, then run the ingestion script.

## How It Works

Spotify's API only provides your last 50 recently played tracks. To build a full history for flashbacks, this tool uses two data sources:

1. **Spotify Data Export** — Your complete listening history (request from Spotify, takes a few days)
2. **Ongoing Polling** — Periodically captures your recent plays to keep the database growing

Both feed into a local SQLite database that the flashback engine queries.

## Built With

- Python 3.10+
- [Spotipy](https://spotipy.readthedocs.io/) — Spotify Web API wrapper
- SQLite — Local listening history database
- [Rich](https://rich.readthedocs.io/) — Beautiful terminal output
- [Click](https://click.palletsprojects.com/) — CLI framework

