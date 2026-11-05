from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    conversation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class AIMessage(Base):
    __tablename__ = "ai_messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversations.conversation_id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AIUsageEvent(Base):
    __tablename__ = "ai_usage_events"
    __table_args__ = (
        CheckConstraint("latency_ms >= 0", name="ck_ai_usage_latency_nonnegative"),
        CheckConstraint("input_tokens IS NULL OR input_tokens >= 0", name="ck_ai_usage_input_tokens_nonnegative"),
        CheckConstraint("output_tokens IS NULL OR output_tokens >= 0", name="ck_ai_usage_output_tokens_nonnegative"),
    )

    event_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AIFeedback(Base):
    __tablename__ = "ai_feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "message_id", name="uq_ai_feedback_user_message"),
        CheckConstraint("rating IN ('helpful', 'not_helpful')", name="ck_ai_feedback_rating"),
    )

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("ai_messages.message_id", ondelete="CASCADE"), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class AIRateLimit(Base):
    __tablename__ = "ai_rate_limits"
    __table_args__ = (CheckConstraint("request_count >= 1", name="ck_ai_rate_limit_count_positive"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
