import ast
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


DATA_DIR = Path("data")
MOVIES_CSV = DATA_DIR / "tmdb_5000_movies.csv"
CREDITS_CSV = DATA_DIR / "tmdb_5000_credits.csv"
MOVIES_PKL = DATA_DIR / "movies_processed.pkl"
SIMILARITY_PKL = DATA_DIR / "similarity.pkl"


def parse_json_column(value):
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError):
        return []


def extract_names(value, limit=None):
    items = parse_json_column(value)
    names = [
        item["name"]
        for item in items
        if isinstance(item, dict) and "name" in item
    ]
    if limit is not None:
        names = names[:limit]
    return names


def extract_director(value):
    items = parse_json_column(value)
    for item in items:
        if isinstance(item, dict) and item.get("job") == "Director":
            return item.get("name", "")
    return ""


def clean_tokens(tokens):
    if not isinstance(tokens, list):
        return []
    return [
        str(token).replace(" ", "").lower()
        for token in tokens
        if str(token).strip()
    ]


def clean_text(text):
    if pd.isna(text):
        return []
    return [word.lower() for word in str(text).split()]


def main():
    if not MOVIES_CSV.exists() or not CREDITS_CSV.exists():
        raise FileNotFoundError(
            "Please place tmdb_5000_movies.csv and tmdb_5000_credits.csv inside the data/ folder."
        )

    print("Loading datasets...")
    movies = pd.read_csv(MOVIES_CSV)
    credits = pd.read_csv(CREDITS_CSV)

    print("Merging datasets...")
    movies = movies.merge(credits, left_on="id", right_on="movie_id")

    print("Selecting useful columns...")
    movies = movies[
        [
            "movie_id",
            "title_x",
            "overview",
            "genres",
            "keywords",
            "cast",
            "crew",
        ]
    ].copy()

    print("Renaming title column...")
    movies.rename(columns={"title_x": "title"}, inplace=True)

    print("Removing rows with missing important values...")
    movies.dropna(subset=["overview", "genres", "keywords", "cast", "crew"], inplace=True)

    print("Extracting metadata...")
    movies["genres_list"] = movies["genres"].apply(
        lambda x: clean_tokens(extract_names(x))
    )
    movies["keywords_list"] = movies["keywords"].apply(
        lambda x: clean_tokens(extract_names(x))
    )
    movies["cast_list"] = movies["cast"].apply(
        lambda x: clean_tokens(extract_names(x, limit=3))
    )
    movies["director_list"] = movies["crew"].apply(
        lambda x: clean_tokens([extract_director(x)])
    )
    movies["overview_list"] = movies["overview"].apply(clean_text)

    print("Building metadata soup...")
    movies["tags_list"] = (
        movies["overview_list"]
        + movies["genres_list"]
        + movies["keywords_list"]
        + movies["cast_list"]
        + movies["director_list"]
    )

    movies["tags"] = movies["tags_list"].apply(lambda x: " ".join(x))
    movies["genres_text"] = movies["genres_list"].apply(lambda x: ", ".join(x))

    # Posters will be added later via API if you want
    movies["poster_url"] = ""

    processed_movies = movies[
        ["movie_id", "title", "tags", "genres_text", "poster_url"]
    ].copy()

    print("Vectorizing tags...")
    cv = CountVectorizer(max_features=5000, stop_words="english")
    vectors = cv.fit_transform(processed_movies["tags"]).toarray()

    print("Calculating cosine similarity...")
    similarity = cosine_similarity(vectors)

    print("Saving processed files...")
    with open(MOVIES_PKL, "wb") as f:
        pickle.dump(processed_movies, f)

    with open(SIMILARITY_PKL, "wb") as f:
        pickle.dump(similarity, f)

    print("Done.")
    print(f"Created: {MOVIES_PKL}")
    print(f"Created: {SIMILARITY_PKL}")


if __name__ == "__main__":
    main()