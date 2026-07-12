import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

TMDB_BEARER_TOKEN = os.getenv("TMDB_BEARER_TOKEN")
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


def fetch_poster_by_title(title: str) -> str:
    if not TMDB_BEARER_TOKEN:
        return ""

    url = f"https://api.themoviedb.org/3/search/movie?query={quote(title)}"
    headers = {
        "Authorization": f"Bearer {TMDB_BEARER_TOKEN}",
        "accept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return ""

        poster_path = results[0].get("poster_path")
        if not poster_path:
            return ""

        return f"{TMDB_IMAGE_BASE}{poster_path}"
    except requests.RequestException:
        return ""