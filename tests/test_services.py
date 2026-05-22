# ============================================================
# NEXUS INTERVIEW - Service Tests
# Tests all Claude service logic and session management
# ============================================================

import pytest
from unittest.mock import MagicMock, patch
from backend.models.schemas import DifficultyLevel, InterviewStatus
from backend.services.claude_service import ClaudeService, sessions


# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def service():
    """Creates a fresh ClaudeService instance for each test."""
    with patch('backend.services.claude_service.anthropic.Anthropic'):
        svc = ClaudeService()
        svc.client = MagicMock()
        return svc


@pytest.fixture
def mock_message_response():
    """Mocks a standard Claude API message response."""
    mock = MagicMock()
    mock.content = [MagicMock(text="Welcome to Nexus Interview. Let's begin.")]
    return mock


@pytest.fixture
def active_session(service, mock_message_response):
    """Creates a live session and returns its session_id."""
    service.client.messages.create.return_value = mock_message_response
    sessions.clear()
    result = service.start_interview(difficulty=DifficultyLevel.BEGINNER)
    return result['session_id']


# ---------------------------
# Start Interview Tests
# ---------------------------

class TestStartInterview:

    def test_start_returns_session_id(self, service, mock_message_response):
        """start_interview should return a valid session_id."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.BEGINNER)
        assert 'session_id' in result
        assert len(result['session_id']) > 0

    def test_start_stores_session(self, service, mock_message_response):
        """start_interview should persist the session in memory."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.BEGINNER)
        assert result['session_id'] in sessions

    def test_start_returns_opening_message(self, service, mock_message_response):
        """start_interview should return the opening message from Claude."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.BEGINNER)
        assert result['message'] == "Welcome to Nexus Interview. Let's begin."

    def test_start_with_custom_topic(self, service, mock_message_response):
        """start_interview should respect a custom topic."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(
            DifficultyLevel.BEGINNER,
            topic="rate limiter"
        )
        assert result['question_topic'] == "rate limiter"

    def test_start_sets_active_status(self, service, mock_message_response):
        """start_interview should set session status to ACTIVE."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.BEGINNER)
        assert result['status'] == InterviewStatus.ACTIVE

    def test_start_initializes_turn_count(self, service, mock_message_response):
        """start_interview should initialize turn_count to zero."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.BEGINNER)
        assert result['turn_count'] == 0

    def test_start_intermediate_difficulty(self, service, mock_message_response):
        """start_interview should handle intermediate difficulty."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.INTERMEDIATE)
        assert result['difficulty'] == DifficultyLevel.INTERMEDIATE

    def test_start_advanced_difficulty(self, service, mock_message_response):
        """start_interview should handle advanced difficulty."""
        service.client.messages.create.return_value = mock_message_response
        sessions.clear()
        result = service.start_interview(DifficultyLevel.ADVANCED)
        assert result['difficulty'] == DifficultyLevel.ADVANCED


# ---------------------------
# Stream Chat Tests
# ---------------------------

class TestStreamChat:

    def test_stream_yields_text(self, service, active_session):
        """stream_chat should yield text chunks."""
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Hello ", "world", "!"])
        service.client.messages.stream.return_value = mock_stream

        chunks = list(service.stream_chat(active_session, "My answer"))
        assert chunks == ["Hello ", "world", "!"]

    def test_stream_increments_turn_count(self, service, active_session):
        """stream_chat should increment the session turn count."""
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["response"])
        service.client.messages.stream.return_value = mock_stream

        list(service.stream_chat(active_session, "My answer"))
        assert sessions[active_session]['turn_count'] == 1

    def test_stream_appends_history(self, service, active_session):
        """stream_chat should append user and assistant messages to history."""
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["response"])
        service.client.messages.stream.return_value = mock_stream

        before = len(sessions[active_session]['history'])
        list(service.stream_chat(active_session, "My answer"))
        after = len(sessions[active_session]['history'])
        assert after == before + 2

    def test_stream_invalid_session_raises(self, service):
        """stream_chat should raise ValueError for unknown session."""
        with pytest.raises(ValueError, match="Session not found"):
            list(service.stream_chat("invalid-id", "test"))

    def test_stream_completed_session_raises(self, service, active_session):
        """stream_chat should raise ValueError if session is not active."""
        sessions[active_session]['status'] = InterviewStatus.COMPLETED
        with pytest.raises(ValueError, match="no longer active"):
            list(service.stream_chat(active_session, "test"))


# ---------------------------
# Hint Tests
# ---------------------------

class TestGetHint:

    def test_hint_returns_string(self, service, active_session, mock_message_response):
        """get_hint should return a non-empty string."""
        mock_message_response.content[0].text = "Think about your bottleneck."
        service.client.messages.create.return_value = mock_message_response
        hint = service.get_hint(active_session)
        assert isinstance(hint, str)
        assert len(hint) > 0

    def test_hint_invalid_session_raises(self, service):
        """get_hint should raise ValueError for unknown session."""
        with pytest.raises(ValueError, match="Session not found"):
            service.get_hint("invalid-id")


# ---------------------------
# Score Tests
# ---------------------------

class TestScoreInterview:

    def test_score_returns_breakdown(self, service, active_session):
        """score_interview should return a valid ScoreBreakdown."""
        import json
        score_json = json.dumps({
            "scalability": 8,
            "reliability": 7,
            "communication": 9,
            "overall": 8,
            "feedback": "Strong performance overall.",
            "strengths": ["Clear thinking", "Good structure"],
            "improvements": ["Address failure cases", "Discuss caching"]
        })
        mock = MagicMock()
        mock.content = [MagicMock(text=score_json)]
        service.client.messages.create.return_value = mock

        result = service.score_interview(active_session)
        assert result['score'].scalability == 8
        assert result['score'].reliability == 7
        assert result['score'].communication == 9
        assert result['score'].overall == 8

    def test_score_marks_session_complete(self, service, active_session):
        """score_interview should mark session as COMPLETED."""
        import json
        score_json = json.dumps({
            "scalability": 7,
            "reliability": 6,
            "communication": 8,
            "overall": 7,
            "feedback": "Decent attempt.",
            "strengths": ["Good start"],
            "improvements": ["Think bigger"]
        })
        mock = MagicMock()
        mock.content = [MagicMock(text=score_json)]
        service.client.messages.create.return_value = mock

        service.score_interview(active_session)
        assert sessions[active_session]['status'] == InterviewStatus.COMPLETED

    def test_score_invalid_session_raises(self, service):
        """score_interview should raise ValueError for unknown session."""
        with pytest.raises(ValueError, match="Session not found"):
            service.score_interview("invalid-id")


# ---------------------------
# Session Helper Tests
# ---------------------------

class TestSessionHelpers:

    def test_get_session_status(self, service, active_session):
        """get_session_status should return correct metadata."""
        result = service.get_session_status(active_session)
        assert result['session_id'] == active_session
        assert result['status'] == InterviewStatus.ACTIVE
        assert result['turn_count'] == 0

    def test_get_session_invalid_raises(self, service):
        """get_session_status should raise for unknown session."""
        with pytest.raises(ValueError, match="Session not found"):
            service.get_session_status("invalid-id")

    def test_end_session_returns_true(self, service, active_session):
        """end_session should return True for a valid session."""
        result = service.end_session(active_session)
        assert result is True

    def test_end_session_marks_abandoned(self, service, active_session):
        """end_session should mark session as ABANDONED."""
        service.end_session(active_session)
        assert sessions[active_session]['status'] == InterviewStatus.ABANDONED

    def test_end_session_invalid_returns_false(self, service):
        """end_session should return False for unknown session."""
        result = service.end_session("invalid-id")
        assert result is False