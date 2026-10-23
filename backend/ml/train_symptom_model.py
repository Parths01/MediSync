from sklearn.metrics import accuracy_score, classification_report

from app.services.symptom_recommender import _MODEL, load_examples


def main() -> None:
    symptoms, labels = load_examples("test")
    predictions = _MODEL.predict(symptoms)
    print("Evaluation uses a small synthetic demo set; results are not clinical validation.")
    print(f"Synthetic holdout accuracy: {accuracy_score(labels, predictions):.3f}")
    print(classification_report(labels, predictions, zero_division=0))


if __name__ == "__main__":
    main()
