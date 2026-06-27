import streamlit as st
from recommender import load_movies, load_similarity, recommend_movies

st.set_page_config(page_title="Movie Matcher", layout="wide")

st.title("🎬 Movie Matcher")
st.write("A simple content-based movie recommender system using metadata similarity.")


@st.cache_resource
def get_data():
    movies = load_movies()
    similarity = load_similarity()
    return movies, similarity


try:
    with st.spinner("Loading movie data..."):
        movies, similarity = get_data()
except FileNotFoundError:
    st.error(
        "Processed files not found. Please run `python3 preprocessing.py` first "
        "after placing the TMDB CSV files in the data/ folder."
    )
    st.stop()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

movie_list = movies["title"].dropna().sort_values().tolist()

selected_movie = st.selectbox("Choose a movie", movie_list)
num_recommendations = st.slider("Number of recommendations", 1, 10, 5)

if st.button("Recommend"):
    with st.spinner("Finding similar movies..."):
        recommendations = recommend_movies(
            selected_movie,
            movies=movies,
            similarity=similarity,
            top_n=num_recommendations,
        )

    if not recommendations:
        st.warning("No recommendations found.")
    else:
        st.subheader("Recommended Movies")

        cols_per_row = 5
        for start in range(0, len(recommendations), cols_per_row):
            row_items = recommendations[start:start + cols_per_row]
            cols = st.columns(len(row_items))

            for col, movie in zip(cols, row_items):
                with col:
                    st.markdown(f"**{movie['title']}**")

                    if movie.get("poster_url"):
                        st.image(movie["poster_url"], use_container_width=True)
                    else:
                        st.info("No poster available")

                    if movie.get("genres_text"):
                        st.caption(f"Genres: {movie['genres_text']}")