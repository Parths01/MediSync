from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = Field(default=None, gt=0)


class Citation(BaseModel):
    title: str
    url: str
    checked_at: str
    passage_id: str | None = None
    source_version: str | None = None
    excerpt: str | None = None


class AIMessageView(BaseModel):
    message_id: int
    role: str
    content: str
    created_at: datetime


class ConversationView(BaseModel):
    conversation_id: int
    title: str
    updated_at: datetime
    messages: list[AIMessageView] = Field(default_factory=list)


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    content: str
    citations: list[Citation]
    emergency: bool
    doctors: list[dict[str, object]] = Field(default_factory=list)


class AIFeedbackCreate(BaseModel):
    rating: Literal["helpful", "not_helpful"]


class AIAnalyticsResponse(BaseModel):
    conversations: int
    requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float | None
    input_tokens: int | None
    output_tokens: int | None
    helpful_feedback: int
    not_helpful_feedback: int
    token_usage_available: bool
