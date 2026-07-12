from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from recommender import load_movies, load_similarity, recommend_movies
from utils.helper import fetch_poster_by_title
from utils.ratings import get_aggregates, load_ratings, save_rating
from utils.svd_model import get_model, predict_for_user

load_dotenv()

app = Flask(__name__)

print("Loading movie data…")
_movies = load_movies()
_similarity = load_similarity()
print(f"✓ {len(_movies)} movies loaded")

_poster_cache: dict = {}


def _get_poster(title: str, existing: str = "") -> str:
    if existing:
        return existing
    if title not in _poster_cache:
        _poster_cache[title] = fetch_poster_by_title(title)
    return _poster_cache[title]


def _batch_posters(titles: list) -> dict:
    missing = [t for t in titles if t not in _poster_cache]
    if missing:
        def _fetch(t: str) -> None:
            _poster_cache[t] = fetch_poster_by_title(t)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(_fetch, missing))
    return {t: _poster_cache.get(t, "") for t in titles}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/movies")
def api_movies():
    search = request.args.get("search", "").strip()
    genre = request.args.get("genre", "").strip()
    limit = min(int(request.args.get("limit", 24)), 48)

    df = _movies.copy()
    if search:
        df = df[df["title"].str.contains(search, case=False, na=False)]
    if genre and genre != "All":
        df = df[df["genres_text"].str.contains(genre, case=False, na=False)]
    df = df.dropna(subset=["title"]).head(limit)

    titles = df["title"].tolist()
    posters = _batch_posters(titles)

    return jsonify([
        {
            "title": row["title"],
            "genres": row.get("genres_text", ""),
            "poster": posters.get(row["title"], ""),
        }
        for _, row in df.iterrows()
    ])


@app.route("/api/genres")
def api_genres():
    genres = sorted({
        g.strip()
        for gs in _movies["genres_text"].dropna()
        for g in gs.split(",")
        if g.strip()
    })
    return jsonify(["All"] + genres)


@app.route("/api/recommend")
def api_recommend():
    title = request.args.get("title", "").strip()
    if not title:
        return jsonify([])
    recs = recommend_movies(title, movies=_movies, similarity=_similarity, top_n=12)
    return jsonify(recs)


@app.route("/api/rate", methods=["POST"])
def api_rate():
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "anonymous")
    title   = data.get("title", "")
    rating  = int(data.get("rating", 0))
    save_rating(user_id, title, rating)
    return jsonify({"ok": True})


@app.route("/api/ratings")
def api_ratings():
    """Aggregate counts per title — used by the UI to show 👍/👎 totals."""
    return jsonify(get_aggregates())


@app.route("/api/ratings/raw")
def api_ratings_raw():
    """Full flat list — used by SurpriseLib in Phase 2."""
    return jsonify(load_ratings())


@app.route("/api/recommend/me")
def api_recommend_me():
    user_id = request.args.get("user_id", "").strip()
    if not user_id:
        return jsonify({"ready": False, "reason": "no user_id"})

    all_ratings  = load_ratings()
    user_ratings = [r for r in all_ratings if r["user_id"] == user_id]

    if len(user_ratings) < 10:
        return jsonify({
            "ready": False,
            "reason": f"Need {10 - len(user_ratings)} more ratings",
        })

    model = get_model(all_ratings)
    if model is None:
        return jsonify({"ready": False, "reason": "Model not ready"})

    already_rated = {r["title"] for r in user_ratings}
    all_titles    = _movies["title"].dropna().tolist()
    top           = predict_for_user(model, user_id, all_titles, already_rated, top_n=12)

    titles  = [p["title"] for p in top]
    posters = _batch_posters(titles)

    results = []
    for pred in top:
        title = pred["title"]
        row   = _movies[_movies["title"] == title]
        if row.empty:
            continue
        row = row.iloc[0]
        results.append({
            "title":     title,
            "genres":    row.get("genres_text", ""),
            "poster":    posters.get(title, ""),
            "svd_score": pred["svd_score"],
        })

    return jsonify({"ready": True, "recommendations": results})


@app.route("/api/ratings/me")
def api_ratings_me():
    """Ratings for a single session user."""
    user_id = request.args.get("user_id", "")
    all_ratings = load_ratings()
    mine = [r for r in all_ratings if r["user_id"] == user_id]
    return jsonify({
        "user_id": user_id,
        "count": len(mine),
        "svd_ready": len(mine) >= 10,
        "ratings": mine,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
