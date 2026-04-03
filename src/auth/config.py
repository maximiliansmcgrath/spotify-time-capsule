"""
Configuration loader for Spotify Time Capsule.
Reads credentials from .env file - never hardcode secrets!
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def load_config() -> dict:
    """Load Spotify credentials from .env file.
    
    Looks for .env in the project root and config/ directory.
    Exits with a helpful message if credentials are missing.
    """
    # Look for .env in project root first, then config/
    project_root = Path(__file__).parent.parent.parent
    env_paths = [
        project_root / ".env",
        project_root / "config" / ".env",
    ]

    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            loaded = True
            break

    if not loaded:
        print("⚠️  No .env file found!")
        print("   Copy config/.env.example to config/.env and add your credentials:")
        print("   cp config/.env.example config/.env")
        sys.exit(1)

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or client_id == "your_client_id_here":
        print("❌ SPOTIFY_CLIENT_ID is missing or still set to placeholder.")
        print("   Edit your .env file and paste in your real Client ID.")
        sys.exit(1)

    if not client_secret or client_secret == "your_client_secret_here":
        print("❌ SPOTIFY_CLIENT_SECRET is missing or still set to placeholder.")
        print("   Edit your .env file and paste in your real Client Secret.")
        sys.exit(1)

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
