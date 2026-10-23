from datetime import datetime, timedelta, timezone

from app.services.heuristics import appointment_follow_up_indicator, classify_feedback


def test_classify_feedback_returns_basic_keyword_sentiment() -> None:
    assert classify_feedback("The doctor was kind and very helpful")["sentiment"] == "positive"
    assert classify_feedback("The wait was long and frustrating")["sentiment"] == "negative"
    assert classify_feedback("My appointment was on Tuesday")["sentiment"] == "neutral"


def test_appointment_follow_up_indicator_combines_only_documented_factors() -> None:
    created_at = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    appointment_date = created_at + timedelta(days=19)
    appointment_date = appointment_date.replace(hour=8)

    result = appointment_follow_up_indicator(
        appointment_date=appointment_date,
        created_at=created_at,
        past_total=3,
        past_cancelled_or_rejected=2,
    )

    assert result["score"] == 0.95
    assert result["label"] == "High"
    assert result["suggestion"] == "Consider a staff-reviewed reminder"
    assert len(result["factors"]) == 4


def test_appointment_follow_up_indicator_does_not_assume_missing_history() -> None:
    appointment_date = datetime(2025, 1, 7, 10, tzinfo=timezone.utc)

    result = appointment_follow_up_indicator(
        appointment_date=appointment_date,
        created_at=None,
        past_total=0,
        past_cancelled_or_rejected=0,
    )

    assert result == {
        "score": 0.0,
        "label": "Low",
        "factors": ["No significant risk factors detected"],
        "suggestion": "No additional reminder suggested by this heuristic",
    }
