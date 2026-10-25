from pathlib import Path

import pytest

from app.services import symptom_recommender
from app.services.symptom_recommender import load_examples, recommend_specialties


def test_recommends_relevant_specialty_from_synthetic_examples() -> None:
    recommendations = recommend_specialties(
        "I have a throbbing headache and sensitivity to bright light"
    )

    assert recommendations
    assert recommendations[0]["specialty"] == "Neurologist"
    assert all(0 <= float(item["score"]) <= 1 for item in recommendations)
    assert len(recommendations) <= 3


def test_returns_no_recommendations_when_text_has_no_known_features() -> None:
    assert recommend_specialties("glimmer florp zindle") == []


def test_recommendations_are_json_safe_and_deterministically_ranked() -> None:
    recommendations = recommend_specialties("I feel unwell with fatigue and a cough")

    assert recommendations
    assert all(type(item["specialty"]) is str for item in recommendations)
    assert all(type(item["score"]) is float for item in recommendations)
    assert [item["score"] for item in recommendations] == sorted(
        (item["score"] for item in recommendations),
        reverse=True,
    )
    assert all(0 <= item["score"] <= 1 for item in recommendations)


def test_rejects_unsupported_dataset_split() -> None:
    with pytest.raises(ValueError, match="Unsupported dataset split"):
        load_examples("validation")


def test_rejects_malformed_dataset_rows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = tmp_path / "malformed.csv"
    dataset.write_text(
        "symptoms,specialty,split\n"
        "headache,Neurologist,train,unexpected\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(symptom_recommender, "TRAINING_DATA_PATH", dataset)

    with pytest.raises(ValueError, match="invalid row"):
        load_examples("train")


def test_training_and_holdout_examples_are_separate_and_cover_same_specialties() -> None:
    _, training_labels = load_examples("train")
    _, test_labels = load_examples("test")

    assert set(training_labels) == set(test_labels)
