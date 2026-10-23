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


def test_training_and_holdout_examples_are_separate_and_cover_same_specialties() -> None:
    _, training_labels = load_examples("train")
    _, test_labels = load_examples("test")

    assert set(training_labels) == set(test_labels)
