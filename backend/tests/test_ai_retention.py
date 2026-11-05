import pytest

from app import cleanup_ai_data
from app.models import AIFeedback, AIConversation, AIMessage


class Result:
    def __init__(self, rowcount: int):
        self.rowcount = rowcount


class CleanupSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return Result(len(self.statements))


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_args):
        return False


class SessionFactory:
    def __init__(self, session):
        self.session = session

    def begin(self):
        return SessionContext(self.session)


@pytest.mark.asyncio
async def test_cleanup_deletes_expired_conversations_and_old_aggregate_events(monkeypatch):
    session = CleanupSession()
    monkeypatch.setattr(cleanup_ai_data, "get_session_factory", lambda: SessionFactory(session))

    deleted_sessions, deleted_conversations, deleted_events, deleted_audits = await cleanup_ai_data.cleanup()

    assert (deleted_sessions, deleted_conversations, deleted_events, deleted_audits) == (1, 2, 3, 4)
    assert len(session.statements) == 4
    assert "DELETE FROM user_sessions" in str(session.statements[0])
    assert "DELETE FROM ai_conversations" in str(session.statements[1])
    assert "DELETE FROM ai_usage_events" in str(session.statements[2])
    assert "DELETE FROM operator_audit_events" in str(session.statements[3])


def test_feedback_and_messages_are_deleted_with_conversation_foreign_key_cascades():
    assert next(iter(AIConversation.__table__.c.user_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(AIMessage.__table__.c.conversation_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(AIFeedback.__table__.c.message_id.foreign_keys)).ondelete == "CASCADE"
