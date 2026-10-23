from datetime import datetime

POSITIVE_FEEDBACK_TERMS = (
    "excellent", "great", "good", "wonderful", "amazing", "fantastic", "perfect",
    "helpful", "kind", "friendly", "professional", "satisfied", "happy", "thank",
    "thanks", "appreciate", "impressed", "love", "best", "outstanding", "superb",
    "brilliant", "pleased", "comfortable", "efficient", "clean", "prompt", "attentive",
    "caring", "polite", "recommend", "awesome", "nice", "positive", "well", "top",
)

NEGATIVE_FEEDBACK_TERMS = (
    "bad", "terrible", "awful", "poor", "horrible", "worst", "disappointing", "rude",
    "unprofessional", "negligent", "slow", "wait", "long wait", "careless", "wrong",
    "mistake", "error", "overcharged", "expensive", "ignored", "unhappy", "unsatisfied",
    "frustrating", "difficult", "problem", "issue", "complaint", "dirty", "unhygienic",
    "late", "delayed", "cancelled", "miss", "never", "not good", "not helpful",
    "not satisfied",
)


def classify_feedback(message: str) -> dict[str, str | int]:
    normalized = message.casefold()
    positive_count = sum(term in normalized for term in POSITIVE_FEEDBACK_TERMS)
    negative_count = sum(term in normalized for term in NEGATIVE_FEEDBACK_TERMS)
    score = positive_count - negative_count
    sentiment = "positive" if score > 0 else "negative" if score < 0 else "neutral"
    return {"sentiment": sentiment, "score": score}


def appointment_follow_up_indicator(
    appointment_date: datetime,
    created_at: datetime | None,
    past_total: int,
    past_cancelled_or_rejected: int,
) -> dict[str, object]:
    score = 0.0
    factors: list[str] = []

    if created_at is not None:
        lead_days = max(0, (appointment_date - created_at).total_seconds() / 86400)
        if lead_days > 14:
            score += 0.25
            factors.append(f"Booked far in advance ({round(lead_days)} days)")
        elif lead_days > 7:
            score += 0.10
            factors.append(f"Booked {round(lead_days)} days ahead")

    if appointment_date.hour < 9 or appointment_date.hour >= 17:
        score += 0.20
        factors.append(f"Off-peak time slot ({appointment_date.strftime('%I:%M %p').lstrip('0')})")

    if appointment_date.weekday() in {0, 4}:
        score += 0.10
        factors.append(f"{appointment_date.strftime('%A')} appointments have higher skip rates")

    if past_total > 0:
        missed_rate = past_cancelled_or_rejected / past_total
        if missed_rate > 0.5:
            score += 0.40
            factors.append(
                f"Patient has {past_cancelled_or_rejected}/{past_total} "
                "past cancelled or rejected appointments"
            )
        elif missed_rate > 0.25:
            score += 0.20
            factors.append(
                f"Patient has some cancelled or rejected past appointments "
                f"({past_cancelled_or_rejected}/{past_total})"
            )

    score = min(1.0, score)
    label = "High" if score >= 0.55 else "Medium" if score >= 0.30 else "Low"
    action = {
        "High": "Consider a staff-reviewed reminder",
        "Medium": "Consider a standard reminder",
        "Low": "No additional reminder suggested by this heuristic",
    }[label]

    return {
        "score": round(score, 2),
        "label": label,
        "factors": factors or ["No significant risk factors detected"],
        "suggestion": action,
    }
