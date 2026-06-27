import pickle
from pathlib import Path
from typing import List, Dict
from utils.helper import fetch_poster_by_title

DATA_DIR = Path("data")
MOVIES_PKL = DATA_DIR / "movies_processed.pkl"
SIMILARITY_PKL = DATA_DIR / "similarity.pkl"


def load_movies():
    if not MOVIES_PKL.exists():
        raise FileNotFoundError(f"{MOVIES_PKL} not found")
    with open(MOVIES_PKL, "rb") as f:
        return pickle.load(f)


def load_similarity():
    if not SIMILARITY_PKL.exists():
        raise FileNotFoundError(f"{SIMILARITY_PKL} not found")
    with open(SIMILARITY_PKL, "rb") as f:
        return pickle.load(f)


def recommend_movies(movie_title: str, movies, similarity, top_n: int = 5) -> List[Dict]:
    match = movies[movies["title"] == movie_title]

    if match.empty:
        return []

    movie_index = match.index[0]
    distances = list(enumerate(similarity[movie_index]))
    distances = sorted(distances, key=lambda x: x[1], reverse=True)

    recommendations = []
    for idx, score in distances[1: top_n + 1]:
        row = movies.iloc[idx]
        title = row.get("title", "")
        poster_url = row.get("poster_url", "")

        if not poster_url:
            poster_url = fetch_poster_by_title(title)

        recommendations.append(
            {
                "title": title,
                "genres_text": row.get("genres_text", ""),
                "poster_url": poster_url,
                "score": float(score),
            }
        )

    return recommendations