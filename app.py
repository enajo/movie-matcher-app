import streamlit as st
from recommender import load_movies, load_similarity, recommend_movies
from utils.ratings import save_rating, get_rating
from utils.helper import fetch_poster_by_title

st.set_page_config(page_title="Movie Matcher", layout="wide", page_icon="🎬")

st.markdown("""
<style>
    .stApp { background-color: #0d0d0d; }
    #MainMenu, footer, header { visibility: hidden; }

    /* Nav */
    .nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.2rem 0 1rem 0;
        border-bottom: 1px solid #1f1f1f;
        margin-bottom: 2rem;
    }
    .nav-logo {
        font-size: 1.4rem;
        font-weight: 800;
        color: #e50914;
        letter-spacing: -0.04em;
    }
    .nav-sub {
        font-size: 0.78rem;
        color: #555;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Search bar */
    .stTextInput > div > div > input {
        background: #1a1a1a !important;
        border: 1px solid #2a2a2a !important;
        border-radius: 0.6rem !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1rem !important;
        caret-color: #e50914;
    }
    .stTextInput > div > div > input:focus {
        border-color: #e50914 !important;
        box-shadow: 0 0 0 2px rgba(229,9,20,0.15) !important;
    }
    .stTextInput label { display: none !important; }

    /* Section heading */
    .section-heading {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.02em;
        margin: 1.75rem 0 1rem 0;
    }
    .section-sub {
        font-size: 0.78rem;
        color: #555;
        margin-top: -0.75rem;
        margin-bottom: 1rem;
    }

    /* Genre pills */
    .genre-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
    }

    /* Movie card */
    .movie-card {
        background: #141414;
        border-radius: 0.75rem;
        overflow: hidden;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 1px solid transparent;
    }
    .movie-card:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 30px rgba(0,0,0,0.6);
        border-color: #333;
    }
    .movie-card.selected {
        border-color: #e50914;
        box-shadow: 0 0 0 2px rgba(229,9,20,0.4);
    }
    .card-placeholder {
        background: #1f1f1f;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        color: #333;
    }
    .card-body { padding: 0.65rem 0.75rem 0.75rem; }
    .card-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: #e5e5e5;
        line-height: 1.35;
        margin-bottom: 0.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .card-genre {
        font-size: 0.7rem;
        color: #666;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .card-rating {
        font-size: 0.7rem;
        color: #555;
        margin-top: 0.35rem;
    }

    /* Selected movie banner */
    .selected-banner {
        background: linear-gradient(135deg, #1a0000 0%, #1a1a1a 100%);
        border: 1px solid #2a0000;
        border-left: 3px solid #e50914;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .selected-banner-label {
        font-size: 0.7rem;
        color: #e50914;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    .selected-banner-title {
        font-size: 1rem;
        font-weight: 700;
        color: #ffffff;
    }

    /* Rating buttons */
    .stButton > button {
        background: #1f1f1f !important;
        border: 1px solid #2a2a2a !important;
        color: #888 !important;
        border-radius: 0.4rem !important;
        font-size: 0.75rem !important;
        padding: 0.2rem 0.5rem !important;
        width: 100% !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        border-color: #e50914 !important;
        color: #fff !important;
    }

    /* Clear button */
    div[data-testid="stVerticalBlock"] { gap: 0 !important; }

    /* No results */
    .no-results {
        text-align: center;
        padding: 3rem;
        color: #444;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_data():
    return load_movies(), load_similarity()

try:
    with st.spinner(""):
        movies, similarity = get_data()
except FileNotFoundError:
    st.error("Run `python3 preprocessing.py` first.")
    st.stop()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

if "rated" not in st.session_state:
    st.session_state.rated = {}
if "selected" not in st.session_state:
    st.session_state.selected = None
if "active_genre" not in st.session_state:
    st.session_state.active_genre = "All"
if "poster_cache" not in st.session_state:
    st.session_state.poster_cache = {}


def get_poster(title: str, existing_url: str = "") -> str:
    if existing_url:
        return existing_url
    if title not in st.session_state.poster_cache:
        st.session_state.poster_cache[title] = fetch_poster_by_title(title)
    return st.session_state.poster_cache[title]

# ── Nav ───────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="nav">
    <span class="nav-logo">MOVIEMATCH</span>
    <span class="nav-sub">Content-based recommendations</span>
</div>
""", unsafe_allow_html=True)

# ── Search bar ────────────────────────────────────────────────────────────────

search = st.text_input("search", placeholder="🔍   Search for a movie title…", label_visibility="hidden")

# ── Genre pills ───────────────────────────────────────────────────────────────

all_genres = sorted(set(
    g.strip()
    for genres in movies["genres_text"].dropna()
    for g in genres.split(",")
    if g.strip()
))

genre_list = ["All"] + all_genres
gcols = st.columns(len(genre_list) if len(genre_list) <= 12 else 12)
for i, genre in enumerate(genre_list[:12]):
    with gcols[i]:
        is_active = st.session_state.active_genre == genre
        label = f"**{genre}**" if is_active else genre
        if st.button(label, key=f"genre_{genre}", use_container_width=True):
            st.session_state.active_genre = genre
            st.session_state.selected = None
            st.rerun()

# ── Filter movies by search + genre ──────────────────────────────────────────

filtered = movies.copy()

if search:
    filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

if st.session_state.active_genre != "All":
    filtered = filtered[
        filtered["genres_text"].str.contains(st.session_state.active_genre, case=False, na=False)
    ]

filtered = filtered.dropna(subset=["title"]).head(24)

# ── Selected movie banner + recommendations ───────────────────────────────────

def render_movie_grid(movie_rows, cols_per_row=6, show_select=True):
    for start in range(0, len(movie_rows), cols_per_row):
        chunk = movie_rows[start: start + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, (_, row) in zip(cols, chunk.iterrows()):
            title = row["title"]
            genres = row.get("genres_text", "")
            poster = row.get("poster_url", "")
            stored = get_rating(title)
            total = stored["up"] + stored["down"]
            is_sel = st.session_state.selected == title

            with col:
                resolved = get_poster(title, poster)
                if resolved:
                    st.image(resolved, use_container_width=True)
                else:
                    st.markdown('<div class="card-placeholder">🎬</div>', unsafe_allow_html=True)

                genre_short = ", ".join(genres.split(",")[:2]) if genres else ""
                rating_txt = f"👍{stored['up']} 👎{stored['down']}" if total > 0 else ""
                selected_marker = " ▶" if is_sel else ""

                st.markdown(f"""
                <div class="card-body">
                    <div class="card-title" title="{title}">{title}{selected_marker}</div>
                    <div class="card-genre">{genre_short}</div>
                    <div class="card-rating">{rating_txt}</div>
                </div>
                """, unsafe_allow_html=True)

                if show_select:
                    btn_label = "▶ Selected" if is_sel else "Find similar"
                    if st.button(btn_label, key=f"sel_{title}_{start}"):
                        st.session_state.selected = None if is_sel else title
                        st.rerun()

                # Rating buttons
                if title in st.session_state.rated:
                    st.markdown('<p style="font-size:0.7rem;color:#444;text-align:center;padding:2px 0 6px">✓ Rated</p>', unsafe_allow_html=True)
                else:
                    r1, r2 = st.columns(2)
                    with r1:
                        if st.button("👍", key=f"up_{title}_{start}"):
                            save_rating(title, 1)
                            st.session_state.rated[title] = 1
                            st.rerun()
                    with r2:
                        if st.button("👎", key=f"dn_{title}_{start}"):
                            save_rating(title, -1)
                            st.session_state.rated[title] = -1
                            st.rerun()


# ── Recommendations ───────────────────────────────────────────────────────────

if st.session_state.selected:
    title = st.session_state.selected
    st.markdown(f"""
    <div class="selected-banner">
        <div>
            <div class="selected-banner-label">Because you picked</div>
            <div class="selected-banner-title">{title}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Finding similar movies…"):
        recs = recommend_movies(title, movies=movies, similarity=similarity, top_n=12)

    if recs:
        st.markdown('<p class="section-heading">More like this</p>', unsafe_allow_html=True)
        import pandas as pd
        rec_df = pd.DataFrame(recs)
        rec_df.index = range(len(rec_df))
        render_movie_grid(rec_df, cols_per_row=6, show_select=False)
    else:
        st.markdown('<div class="no-results">No similar movies found.</div>', unsafe_allow_html=True)

    st.markdown("---")

# ── Browse grid ───────────────────────────────────────────────────────────────

heading = f'Search results for "{search}"' if search else (
    f"{st.session_state.active_genre} Movies" if st.session_state.active_genre != "All" else "Browse All"
)
st.markdown(f'<p class="section-heading">{heading}</p>', unsafe_allow_html=True)

if filtered.empty:
    st.markdown('<div class="no-results">No movies found. Try a different search.</div>', unsafe_allow_html=True)
else:
    render_movie_grid(filtered, cols_per_row=6)
