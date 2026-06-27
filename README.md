
# Movie Matcher

Movie Matcher is a lightweight content-based recommendation system that suggests similar movies based on metadata such as genres, keywords, cast, and director.

The application uses a simple NLP pipeline to transform movie metadata into vector representations and computes similarity using cosine distance. A minimal web interface built with Streamlit allows users to select a movie and receive relevant recommendations instantly.

## Getting Started

Clone the repository and set up a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# or
source .venv/bin/activate  # Linux / WSL
````

Install dependencies:

```bash
pip install -r requirements.txt
```

Place the TMDB 5000 dataset (`tmdb_5000_movies.csv`, `tmdb_5000_credits.csv`) inside the `data/` directory, then run:

```bash
python preprocessing.py
```

Start the application:

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Notes

* The recommendation engine is based on metadata similarity, not user behavior.
* Preprocessing generates serialized data files (`.pkl`) for faster runtime performance.
* Poster support can be added via external APIs if needed.

## License

This project is intended for educational and demonstration purposes.

```