import csv
from pathlib import Path
from typing import TypedDict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


TRAINING_DATA_PATH = (
    Path(__file__).resolve().parents[2] / "ml" / "synthetic_symptom_examples.csv"
)
VALID_SPLITS = {"train", "test"}


class SpecialtySuggestion(TypedDict):
    specialty: str
    score: float


def load_examples(split: str) -> tuple[list[str], list[str]]:
    if split not in VALID_SPLITS:
        raise ValueError(f"Unsupported dataset split: {split}")

    symptoms: list[str] = []
    specialties: list[str] = []

    with TRAINING_DATA_PATH.open(encoding="utf-8", newline="") as dataset:
        rows = csv.DictReader(dataset)
        if rows.fieldnames != ["symptoms", "specialty", "split"]:
            raise ValueError("Synthetic symptom dataset has an invalid header")

        for row in rows:
            if None in row or any(row.get(field) is None for field in rows.fieldnames):
                raise ValueError("Synthetic symptom dataset contains an invalid row")

            description = row["symptoms"].strip()
            specialty = row["specialty"].strip()
            row_split = row["split"].strip()
            if not description or not specialty:
                raise ValueError("Synthetic symptom dataset contains an empty field")
            if row_split not in VALID_SPLITS:
                raise ValueError("Synthetic symptom dataset contains an invalid split")
            if row_split != split:
                continue

            symptoms.append(description)
            specialties.append(specialty)

    if not symptoms:
        raise ValueError(f"Synthetic symptom dataset has no {split} examples")
    return symptoms, specialties


def train_model() -> Pipeline:
    symptoms, specialties = load_examples("train")
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
            ("classifier", MultinomialNB(alpha=0.5)),
        ]
    )
    model.fit(symptoms, specialties)
    return model


_MODEL = train_model()


def recommend_specialties(symptoms: str) -> list[SpecialtySuggestion]:
    normalized = symptoms.strip()
    if not normalized:
        return []

    vectorizer: TfidfVectorizer = _MODEL.named_steps["tfidf"]
    if vectorizer.transform([normalized]).nnz == 0:
        return []

    probabilities = _MODEL.predict_proba([normalized])[0]
    ranked = sorted(
        zip(_MODEL.classes_, probabilities, strict=True),
        key=lambda item: (-float(item[1]), str(item[0]).casefold()),
    )
    return [
        {"specialty": str(specialty), "score": round(float(score), 4)}
        for specialty, score in ranked[:3]
    ]
