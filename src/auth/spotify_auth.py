"""
Spotify OAuth authentication handler.
Uses Authorization Code flow to get user-level access (needed for listening history).
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from src.auth.config import load_config


# Scopes define what your app can access
# user-read-recently-played: needed for polling recent tracks
# user-top-read: needed for top artists/tracks
# user-read-playback-state: see what's currently playing
SCOPES = [
    "user-read-recently-played",
    "user-top-read",
    "user-read-playback-state",
    "user-read-currently-playing",
    "user-read-private",
    "user-modify-playback-state",
]


def get_spotify_client() -> spotipy.Spotify:
    """Create an authenticated Spotify client.
    
    On first run, this opens a browser for you to log in.
    After that, it caches the token and refreshes automatically.
    """
    config = load_config()

    auth_manager = SpotifyOAuth(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        redirect_uri=config["redirect_uri"],
        scope=" ".join(SCOPES),
        cache_path=".spotify_cache",
        open_browser=True,
    )

    return spotipy.Spotify(auth_manager=auth_manager)


def test_connection():
    """Quick test to verify your credentials work."""
    try:
        sp = get_spotify_client()
        user = sp.current_user()
        print(f"✅ Connected as: {user['display_name']} ({user['id']})")
        print(f"   Account type: {user['product']}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
