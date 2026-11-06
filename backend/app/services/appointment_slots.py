"""Shared booking window and half-hour slot rules for appointments."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


APPOINTMENT_TIMEZONE = ZoneInfo("Asia/Kolkata")
BOOKING_WINDOW_DAYS = 30
SLOT_MINUTES = 30
OPENING_MINUTE = 9 * 60
CLOSING_MINUTE = 17 * 60


def scheduled_slots(
    *,
    days: int = BOOKING_WINDOW_DAYS,
    now: datetime | None = None,
) -> dict[date, list[datetime]]:
    """Return future half-hour start times for the configured clinic window."""
    current = (now or datetime.now(APPOINTMENT_TIMEZONE)).astimezone(APPOINTMENT_TIMEZONE)
    result: dict[date, list[datetime]] = {}

    for offset in range(days):
        clinic_date = current.date() + timedelta(days=offset)
        if clinic_date.weekday() == 6:  # Sunday
            continue

        slots: list[datetime] = []
        for minute_of_day in range(OPENING_MINUTE, CLOSING_MINUTE, SLOT_MINUTES):
            slot = datetime.combine(
                clinic_date,
                time(minute_of_day // 60, minute_of_day % 60),
                tzinfo=APPOINTMENT_TIMEZONE,
            )
            if slot > current:
                slots.append(slot)
        if slots:
            result[clinic_date] = slots

    return result


def is_scheduled_slot(value: datetime, *, now: datetime | None = None) -> bool:
    """Validate a submitted timestamp against the same India-time schedule."""
    if value.tzinfo is None or value.utcoffset() is None:
        return False

    current = (now or datetime.now(APPOINTMENT_TIMEZONE)).astimezone(APPOINTMENT_TIMEZONE)
    local_value = value.astimezone(APPOINTMENT_TIMEZONE)
    minute_of_day = local_value.hour * 60 + local_value.minute

    return (
        current.date() <= local_value.date() < current.date() + timedelta(days=BOOKING_WINDOW_DAYS)
        and local_value.weekday() != 6
        and local_value.second == 0
        and local_value.microsecond == 0
        and OPENING_MINUTE <= minute_of_day < CLOSING_MINUTE
        and minute_of_day % SLOT_MINUTES == 0
        and local_value > current
    )
