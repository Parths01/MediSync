from datetime import datetime

from pydantic import BaseModel

from app.schemas.patient import AppointmentView, ContactStatus


class MonthlyCount(BaseModel):
    month: str
    count: int


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_doctors: int
    total_appointments: int
    new_users_30d: int
    pending_appointments: int
    appointment_status_counts: dict[str, int]
    monthly_appointments: list[MonthlyCount]
    monthly_registrations: list[MonthlyCount]
    recent_appointments: list[AppointmentView]


class ContactStatusUpdate(BaseModel):
    status: ContactStatus


class AppointmentFollowUpView(BaseModel):
    appointment: AppointmentView
    indicator_score: float
    indicator_label: str
    factors: list[str]
    suggestion: str


class FeedbackInsightView(BaseModel):
    feedback_id: int
    message: str
    created_at: datetime | None
    user_name: str
    sentiment: str


class AdminInsightsResponse(BaseModel):
    follow_up_indicators: list[AppointmentFollowUpView]
    feedback_total: int
    feedback_analyzed: int
    sentiment_counts: dict[str, int]
    negative_feedback: list[FeedbackInsightView]
    disclaimer: str
