import json
import time
from pathlib import Path

RATINGS_FILE = Path("data/ratings.json")


def load_ratings() -> list:
    """Return all ratings as a flat list of {user_id, title, rating, ts}."""
    if not RATINGS_FILE.exists():
        return []
    with open(RATINGS_FILE) as f:
        data = json.load(f)
    # Migrate old dict format gracefully
    if isinstance(data, dict):
        return []
    return data


def save_rating(user_id: str, title: str, rating: int) -> None:
    ratings = load_ratings()
    # Remove any existing rating from this user for this title (allow re-rating)
    ratings = [r for r in ratings if not (r["user_id"] == user_id and r["title"] == title)]
    ratings.append({
        "user_id": user_id,
        "title": title,
        "rating": rating,
        "ts": int(time.time()),
    })
    with open(RATINGS_FILE, "w") as f:
        json.dump(ratings, f, indent=2)


def get_aggregates() -> dict:
    """Return {title: {up: N, down: N}} for display on cards."""
    agg: dict = {}
    for r in load_ratings():
        t = r["title"]
        if t not in agg:
            agg[t] = {"up": 0, "down": 0}
        if r["rating"] == 1:
            agg[t]["up"] += 1
        else:
            agg[t]["down"] += 1
    return agg
