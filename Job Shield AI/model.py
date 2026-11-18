

import pandas as pd
import re
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Simple stop‑word list (common English stopwords)
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "while", "with",
    "for", "on", "at", "by", "from", "up", "out", "about", "into",
    "over", "after", "before", "under", "above", "to", "of", "in",
    "is", "are", "was", "were", "be", "been", "being", "has", "have",
    "had", "do", "does", "did", "will", "would", "should", "can", "could",
    "may", "might", "must",
}

def _clean_text(text: str) -> str:
    """Lower‑case, strip punctuation, and remove stop‑words.
    This mirrors the preprocessing used in the Streamlit app.
    """
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Replace any character that is not a word character or whitespace with a space
    text = re.sub(r"[^\w\s]", " ", text)
    words = [w for w in text.split() if w not in STOPWORDS]
    return " ".join(words)

def load_dataset(csv_path: Path) -> pd.DataFrame:
    """Load the CSV and create a cleaned text column for training."""
    df = pd.read_csv(csv_path)
    df["combined_text"] = (
        df["title"].fillna("") + " " +
        df["company_profile"].fillna("") + " " +
        df["description"].fillna("") + " " +
        df["requirements"].fillna("")
    )
    df["clean_text"] = df["combined_text"].apply(_clean_text)
    return df

def train_and_save(csv_path: Path, model_path: Path):
    """Train a Logistic Regression model and persist it with its vectorizer.
    The artefact is saved as a dict: {"model": clf, "vectorizer": vec}
    """
    df = load_dataset(csv_path)
    X = df["clean_text"]
    y = df["fraudulent"]
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_vec = vectorizer.fit_transform(X)
    clf = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        solver="liblinear",
        random_state=42,
    )
    clf.fit(X_vec, y)
    joblib.dump({"model": clf, "vectorizer": vectorizer}, model_path)
    print(f"Model saved to {model_path}")

def load_model(model_path: Path):
    """Load persisted model and vectorizer. Returns (model, vectorizer) or (None, None)."""
    if not model_path.exists():
        return None, None
    data = joblib.load(model_path)
    return data["model"], data["vectorizer"]

def predict_proba(text: str, model, vectorizer) -> float:
    """Return the fraud probability (0‑1) for a raw text string.
    The text is pre‑processed with the same routine used during training.
    """
    cleaned = _clean_text(text)
    X_vec = vectorizer.transform([cleaned])
    return model.predict_proba(X_vec)[0][1]

if __name__ == "__main__":
    csv_file = Path(__file__).parent / "sample_data.csv"
    model_file = Path(__file__).parent / "fake_job_model.joblib"
    train_and_save(csv_file, model_file)
