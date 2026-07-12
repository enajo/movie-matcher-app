from __future__ import annotations

import pandas as pd
from surprise import SVD, Dataset, Reader

# ── Cached model ───────────────────────────────────────────────────────────────
# Retrained automatically whenever the rating count changes.

_model = None
_trained_on: int = 0   # number of ratings the model was last trained on


def train(ratings: list) -> SVD | None:
    """Train SVD on the full ratings list. Returns None if not enough data."""
    if len(ratings) < 5:
        return None
    df = pd.DataFrame(ratings)[["user_id", "title", "rating"]]
    reader = Reader(rating_scale=(-1, 1))
    data = Dataset.load_from_df(df, reader)
    model = SVD(n_factors=50, n_epochs=25, lr_all=0.005, reg_all=0.02)
    model.fit(data.build_full_trainset())
    return model


def get_model(ratings: list) -> SVD | None:
    """Return a cached model, retraining only when rating count changes."""
    global _model, _trained_on
    if len(ratings) != _trained_on:
        print(f"[SVD] Retraining on {len(ratings)} ratings…")
        _model = train(ratings)
        _trained_on = len(ratings)
    return _model


def predict_for_user(
    model: SVD,
    user_id: str,
    all_titles: list,
    already_rated: set,
    top_n: int = 12,
) -> list[dict]:
    """
    Score every unrated movie for this user and return the top N.
    Returns list of {title, svd_score}.
    """
    preds = []
    for title in all_titles:
        if title in already_rated:
            continue
        est = model.predict(user_id, title).est
        preds.append({"title": title, "svd_score": round(est, 4)})
    preds.sort(key=lambda x: x["svd_score"], reverse=True)
    return preds[:top_n]
