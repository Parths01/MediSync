import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import case, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import AIFeedback, AIConversation, AIMessage, AIRateLimit, AIUsageEvent, Doctor, User
from app.schemas.ai import AIFeedbackCreate, ChatRequest, ChatResponse, Citation, ConversationView
from app.security import get_current_user, require_csrf, require_session_cookie
from app.services.ai_assistant import build_context, detect_emergency, emergency_response, freshness_status
from app.services.llm import LLMResult, ProviderTransientError, ProviderUnavailable, get_llm_service

router = APIRouter(prefix="/ai", tags=["AI assistant"], dependencies=[Depends(require_csrf), Depends(require_session_cookie)])
logger = logging.getLogger(__name__)


async def require_ai_patient_data_enabled() -> None:
    if not get_settings().ai_patient_data_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI chat is disabled for this deployment",
        )


async def _enforce_rate_limit(db: AsyncSession, user_id: int) -> None:
    now = datetime.now(timezone.utc)
    window_start = now.replace(second=0, microsecond=0)
    same_window = AIRateLimit.window_started_at == window_start
    statement = (
        pg_insert(AIRateLimit)
        .values(user_id=user_id, window_started_at=window_start, request_count=1)
        .on_conflict_do_update(
            index_elements=[AIRateLimit.user_id],
            set_={
                "window_started_at": case((same_window, AIRateLimit.window_started_at), else_=window_start),
                "request_count": case((same_window, AIRateLimit.request_count + 1), else_=1),
            },
        )
        .returning(AIRateLimit.request_count)
    )
    result = await db.execute(statement)
    if result.scalar_one() > 20:
        raise HTTPException(status_code=429, detail="Please wait before sending another message")


async def _respond(
    payload: ChatRequest,
    db: AsyncSession,
    user: User,
    stream_sink: Callable[[str, str], Awaitable[None]] | None = None,
) -> ChatResponse:
    conversation = None
    if payload.conversation_id is not None:
        result = await db.execute(select(AIConversation).where(
            AIConversation.conversation_id == payload.conversation_id,
            AIConversation.user_id == user.user_id,
            AIConversation.expires_at > datetime.now(timezone.utc),
        ))
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        history_result = await db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation.conversation_id)
            .order_by(AIMessage.message_id.desc())
            .limit(get_settings().ai_context_max_messages)
        )
        history = list(reversed(history_result.scalars().all()))
        context = build_context(
            [{"role": item.role, "content": item.content} for item in history],
            max_messages=get_settings().ai_context_max_messages,
            max_chars=get_settings().ai_context_max_chars,
        )
    else:
        context = []

    await _enforce_rate_limit(db, user.user_id)
    await db.commit()

    if conversation is None:
        conversation = AIConversation(
            user_id=user.user_id,
            title=payload.message[:100],
            expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().ai_conversation_retention_days),
        )
        db.add(conversation)
        await db.flush()

    user_message = AIMessage(conversation_id=conversation.conversation_id, role="user", content=payload.message)
    if detect_emergency(payload.message):
        content, sources = emergency_response()
        emergency = True
        if stream_sink is not None:
            await stream_sink(content, "buffered")
    else:
        try:
            service = get_llm_service()
            if stream_sink is None:
                generated = await service.generate(payload.message, context)
            else:
                chunks: list[str] = []
                sources = []
                stream = service.stream(payload.message, context)
                try:
                    async for chunk in stream:
                        sources = chunk.citations or sources
                        if chunk.text:
                            chunks.append(chunk.text)
                            await stream_sink(chunk.text, chunk.delivery_mode)
                finally:
                    await stream.aclose()
                generated = LLMResult(content="".join(chunks), citations=sources)
        except (ProviderUnavailable, ProviderTransientError, TimeoutError) as error:
            raise HTTPException(status_code=503, detail="Assistant is temporarily unavailable") from error
        except Exception as error:
            logger.warning("AI provider adapter failed (%s)", type(error).__name__)
            raise HTTPException(status_code=503, detail="Assistant is temporarily unavailable") from error
        content, sources, emergency = generated.content, generated.citations, False
    assistant_message = AIMessage(conversation_id=conversation.conversation_id, role="assistant", content=content)
    db.add_all([user_message, assistant_message])
    conversation.updated_at = datetime.now(timezone.utc)
    conversation.expires_at = conversation.updated_at + timedelta(days=get_settings().ai_conversation_retention_days)
    await db.commit()
    await db.refresh(assistant_message)

    doctors: list[dict[str, object]] = []
    if not emergency:
        text = payload.message.casefold()
        specialty_terms = {
            "eye": ("ophthalm", "optomet"), "vision": ("ophthalm", "optomet"),
            "skin": ("dermatolog",), "rash": ("dermatolog",),
            "tooth": ("dent",), "dental": ("dent",),
            "ear": ("otolaryng", "ent"), "hearing": ("otolaryng", "ent"),
            "joint": ("orthop", "rheumat"), "bone": ("orthop",),
            "stomach": ("gastro",), "digest": ("gastro",),
            "heart": ("cardio",), "pregnan": ("obstetric", "gynecol"),
        }
        matched = {term for keyword, terms in specialty_terms.items() if keyword in text for term in terms}
        if matched:
            clauses = [Doctor.specialization.ilike(f"%{term}%") for term in matched]
            result = await db.execute(select(Doctor).where(or_(*clauses)).order_by(Doctor.name).limit(8))
            doctors = [{"doctor_id": d.doctor_id, "name": d.name, "specialization": d.specialization, "experience": d.experience} for d in result.scalars()]
    return ChatResponse(
        conversation_id=conversation.conversation_id,
        message_id=assistant_message.message_id,
        content=content,
        citations=[Citation(title=s.title, url=s.url, checked_at=freshness_status()) for s in sources],
        emergency=emergency,
        doctors=doctors,
    )


async def _tracked_respond(
    payload: ChatRequest,
    db: AsyncSession,
    user: User,
    stream_sink: Callable[[str, str], Awaitable[None]] | None = None,
) -> ChatResponse:
    started = time.perf_counter()
    try:
        result = await _respond(payload, db, user, stream_sink=stream_sink)
    except Exception as error:
        try:
            await db.rollback()
        except Exception:
            logger.warning("AI request transaction could not be rolled back")
        db.add(AIUsageEvent(
            provider="local_rules",
            succeeded=False,
            latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
        ))
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            logger.warning("AI usage failure event could not be persisted (%s)", type(error).__name__)
        else:
            logger.warning("AI request failed (%s)", type(error).__name__)
        raise

    db.add(AIUsageEvent(
        provider="local_rules",
        succeeded=True,
        latency_ms=max(0, round((time.perf_counter() - started) * 1000)),
        input_tokens=None,
        output_tokens=None,
    ))
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        logger.warning("AI usage success event could not be persisted")
    return result


@router.get("/conversations", response_model=list[ConversationView])
async def list_conversations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(AIConversation).where(
        AIConversation.user_id == user.user_id,
        AIConversation.expires_at > datetime.now(timezone.utc),
    ).order_by(AIConversation.updated_at.desc()).limit(50))
    return [{"conversation_id": c.conversation_id, "title": c.title, "updated_at": c.updated_at, "messages": []} for c in result.scalars()]


@router.get("/conversations/{conversation_id}", response_model=ConversationView)
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(AIConversation).where(
        AIConversation.conversation_id == conversation_id,
        AIConversation.user_id == user.user_id,
        AIConversation.expires_at > datetime.now(timezone.utc),
    ))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = await db.execute(select(AIMessage).where(AIMessage.conversation_id == conversation_id).order_by(AIMessage.message_id.desc()).limit(100))
    ordered_messages = list(reversed(messages.scalars().all()))
    return {"conversation_id": conversation.conversation_id, "title": conversation.title, "updated_at": conversation.updated_at, "messages": ordered_messages}


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(AIConversation).where(AIConversation.conversation_id == conversation_id, AIConversation.user_id == user.user_id))
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conversation)


@router.delete("/conversations", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_conversations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Patient-requested deletion; FK cascades remove messages and linked feedback."""
    await db.execute(
        AIConversation.__table__.delete().where(AIConversation.user_id == user.user_id)
    )


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_ai_patient_data_enabled)])
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _tracked_respond(payload, db, user)


@router.post("/chat/stream", dependencies=[Depends(require_ai_patient_data_enabled)])
async def chat_stream(payload: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    queue: asyncio.Queue[tuple[str, object]] = asyncio.Queue(maxsize=32)
    stream_modes: set[str] = set()

    async def stream_sink(text: str, delivery_mode: str) -> None:
        stream_modes.add(delivery_mode)
        await queue.put(("content", (text, delivery_mode)))

    async def produce() -> None:
        try:
            result = await _tracked_respond(payload, db, user, stream_sink=stream_sink)
        except HTTPException as error:
            await queue.put(("error", (error.status_code, "Assistant is temporarily unavailable")))
        except Exception:
            await queue.put(("error", (503, "Assistant is temporarily unavailable")))
        else:
            mode = "provider_stream" if "provider_stream" in stream_modes else "buffered"
            await queue.put(("complete", (result, mode)))

    task = asyncio.create_task(produce())
    first = await queue.get()
    if first[0] == "error":
        await task
        code, detail = first[1]
        raise HTTPException(status_code=code, detail=detail)

    async def events():
        current = first
        try:
            while True:
                kind, value = current
                if kind == "content":
                    text, delivery_mode = value
                    event_type = "response" if delivery_mode == "buffered" else "delta"
                    yield f"data: {json.dumps({'type': event_type, 'text': text})}\n\n"
                elif kind == "error":
                    code, detail = value
                    yield f"data: {json.dumps({'type': 'error', 'status': code, 'detail': detail})}\n\n"
                    return
                elif kind == "complete":
                    result, delivery_mode = value
                    yield f"data: {json.dumps({'type': 'metadata', 'conversation_id': result.conversation_id, 'message_id': result.message_id, 'citations': [c.model_dump() for c in result.citations], 'emergency': result.emergency, 'doctors': result.doctors, 'delivery_mode': delivery_mode})}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                current = await queue.get()
        finally:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post(
    "/messages/{message_id}/feedback",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_ai_patient_data_enabled)],
)
async def submit_feedback(
    message_id: int,
    payload: AIFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AIMessage)
        .join(AIConversation, AIConversation.conversation_id == AIMessage.conversation_id)
        .where(
            AIMessage.message_id == message_id,
            AIMessage.role == "assistant",
            AIConversation.user_id == user.user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Assistant message not found")
    db.add(AIFeedback(user_id=user.user_id, message_id=message_id, rating=payload.rating))
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Feedback was already submitted") from error
    return {"status": "received"}
