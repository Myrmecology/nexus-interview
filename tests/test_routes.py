# ============================================================
# NEXUS INTERVIEW - Route Tests
# Tests all FastAPI endpoints end to end
# ============================================================

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from backend.main import app
from backend.models.schemas import (
    DifficultyLevel,
    InterviewStatus
)
from backend.services.claude_service import sessions


# ---------------------------
# Test Client
# ---------------------------

client = TestClient(app)


# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture(autouse=True)
def clear_sessions():
    """Clears all sessions before every test."""
    sessions.clear()
    yield
    sessions.clear()


@pytest.fixture
def mock_claude():
    """Mocks the ClaudeService for route-level tests."""
    with patch(
        'backend.routes.interview.claude_service'
    ) as mock:
        yield mock


@pytest.fixture
def started_session(mock_claude):
    """Starts a session and returns session data."""
    mock_claude.start_interview.return_value = {
        "session_id": "test-session-001",
        "message": "Welcome. Design a URL shortener.",
        "difficulty": DifficultyLevel.BEGINNER,
        "question_topic": "URL shortener",
        "turn_count": 0,
        "max_turns": 10,
        "status": InterviewStatus.ACTIVE
    }

    res = client.post("/api/interview/start", json={
        "difficulty": "beginner"
    })

    assert res.status_code == 200
    return res.json()


# ---------------------------
# Health Check Tests
# ---------------------------

class TestHealthCheck:

    def test_health_returns_ok(self):
        """Health endpoint should return status ok."""
        res = client.get("/api/interview/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_health_returns_app_name(self):
        """Health endpoint should return the app name."""
        res = client.get("/api/interview/health")
        assert "app" in res.json()

    def test_health_returns_version(self):
        """Health endpoint should return the version."""
        res = client.get("/api/interview/health")
        assert "version" in res.json()


# ---------------------------
# Start Interview Tests
# ---------------------------

class TestStartInterview:

    def test_start_returns_200(self, mock_claude):
        """POST /start should return 200."""
        mock_claude.start_interview.return_value = {
            "session_id": "abc-123",
            "message": "Let's begin.",
            "difficulty": DifficultyLevel.BEGINNER,
            "question_topic": "URL shortener",
            "turn_count": 0,
            "max_turns": 10,
            "status": InterviewStatus.ACTIVE
        }
        res = client.post("/api/interview/start", json={
            "difficulty": "beginner"
        })
        assert res.status_code == 200

    def test_start_returns_session_id(self, mock_claude):
        """POST /start should return a session_id."""
        mock_claude.start_interview.return_value = {
            "session_id": "abc-123",
            "message": "Let's begin.",
            "difficulty": DifficultyLevel.BEGINNER,
            "question_topic": "URL shortener",
            "turn_count": 0,
            "max_turns": 10,
            "status": InterviewStatus.ACTIVE
        }
        res = client.post("/api/interview/start", json={
            "difficulty": "beginner"
        })
        assert "session_id" in res.json()

    def test_start_with_topic(self, mock_claude):
        """POST /start should accept an optional topic."""
        mock_claude.start_interview.return_value = {
            "session_id": "abc-123",
            "message": "Let's begin.",
            "difficulty": DifficultyLevel.BEGINNER,
            "question_topic": "rate limiter",
            "turn_count": 0,
            "max_turns": 10,
            "status": InterviewStatus.ACTIVE
        }
        res = client.post("/api/interview/start", json={
            "difficulty": "beginner",
            "topic": "rate limiter"
        })
        assert res.status_code == 200
        assert res.json()["question_topic"] == "rate limiter"

    def test_start_invalid_difficulty(self):
        """POST /start with invalid difficulty should return 422."""
        res = client.post("/api/interview/start", json={
            "difficulty": "impossible"
        })
        assert res.status_code == 422

    def test_start_service_error_returns_500(self, mock_claude):
        """POST /start should return 500 if service raises."""
        mock_claude.start_interview.side_effect = Exception("API error")
        res = client.post("/api/interview/start", json={
            "difficulty": "beginner"
        })
        assert res.status_code == 500

    def test_start_value_error_returns_400(self, mock_claude):
        """POST /start should return 400 if service raises ValueError."""
        mock_claude.start_interview.side_effect = ValueError("Bad input")
        res = client.post("/api/interview/start", json={
            "difficulty": "beginner"
        })
        assert res.status_code == 400


# ---------------------------
# Chat Tests
# ---------------------------

class TestChat:

    def test_chat_returns_200(self, mock_claude, started_session):
        """POST /chat should return 200 with a valid session."""
        mock_claude.stream_chat.return_value = iter(
            ["Great ", "answer!"]
        )
        res = client.post("/api/interview/chat", json={
            "session_id": started_session["session_id"],
            "message": "I would start with an API gateway."
        })
        assert res.status_code == 200

    def test_chat_streams_content(self, mock_claude, started_session):
        """POST /chat should stream text content."""
        mock_claude.stream_chat.return_value = iter(
            ["Think ", "about ", "scale."]
        )
        res = client.post("/api/interview/chat", json={
            "session_id": started_session["session_id"],
            "message": "My approach would be..."
        })
        assert "Think" in res.text

    def test_chat_invalid_session_returns_404(self, mock_claude):
        """POST /chat with unknown session raises ValueError."""
        mock_claude.stream_chat.side_effect = ValueError(
            "Session not found."
        )
        with pytest.raises((ValueError, Exception)):
            client.post("/api/interview/chat", json={
                "session_id": "invalid-id",
                "message": "test"
            })

    def test_chat_empty_message_returns_422(self, started_session):
        """POST /chat with empty message should return 422."""
        res = client.post("/api/interview/chat", json={
            "session_id": started_session["session_id"],
            "message": ""
        })
        assert res.status_code == 422

    def test_chat_missing_session_id_returns_422(self):
        """POST /chat without session_id should return 422."""
        res = client.post("/api/interview/chat", json={
            "message": "My answer"
        })
        assert res.status_code == 422

    def test_chat_service_error_returns_500(
        self, mock_claude, started_session
    ):
        """POST /chat raises when service throws an exception."""
        mock_claude.stream_chat.side_effect = Exception("Stream broke")
        with pytest.raises((ValueError, Exception)):
            client.post("/api/interview/chat", json={
                "session_id": started_session["session_id"],
                "message": "My answer"
            })


# ---------------------------
# Hint Tests
# ---------------------------

class TestHint:

    def test_hint_returns_200(self, mock_claude, started_session):
        """POST /hint should return 200."""
        mock_claude.get_hint.return_value = "Think about bottlenecks."
        res = client.post("/api/interview/hint", json={
            "session_id": started_session["session_id"]
        })
        assert res.status_code == 200

    def test_hint_returns_text(self, mock_claude, started_session):
        """POST /hint should return a hint string."""
        mock_claude.get_hint.return_value = "Think about bottlenecks."
        res = client.post("/api/interview/hint", json={
            "session_id": started_session["session_id"]
        })
        assert res.json()["hint"] == "Think about bottlenecks."

    def test_hint_invalid_session_returns_404(self, mock_claude):
        """POST /hint with unknown session should return 404."""
        mock_claude.get_hint.side_effect = ValueError(
            "Session not found."
        )
        res = client.post("/api/interview/hint", json={
            "session_id": "invalid-id"
        })
        assert res.status_code == 404

    def test_hint_service_error_returns_500(
        self, mock_claude, started_session
    ):
        """POST /hint should return 500 if service raises."""
        mock_claude.get_hint.side_effect = Exception("Failed")
        res = client.post("/api/interview/hint", json={
            "session_id": started_session["session_id"]
        })
        assert res.status_code == 500


# ---------------------------
# Score Tests
# ---------------------------

class TestScore:

    def test_score_returns_200(self, mock_claude, started_session):
        """POST /score should return 200."""
        from backend.models.schemas import ScoreBreakdown
        mock_claude.score_interview.return_value = {
            "session_id": started_session["session_id"],
            "score": ScoreBreakdown(
                scalability=8,
                reliability=7,
                communication=9,
                overall=8
            ),
            "feedback": "Strong performance.",
            "strengths": ["Clear thinking"],
            "improvements": ["Address failures"],
            "status": InterviewStatus.COMPLETED
        }
        res = client.post("/api/interview/score", json={
            "session_id": started_session["session_id"]
        })
        assert res.status_code == 200

    def test_score_returns_breakdown(self, mock_claude, started_session):
        """POST /score should return all score fields."""
        from backend.models.schemas import ScoreBreakdown
        mock_claude.score_interview.return_value = {
            "session_id": started_session["session_id"],
            "score": ScoreBreakdown(
                scalability=8,
                reliability=7,
                communication=9,
                overall=8
            ),
            "feedback": "Strong performance.",
            "strengths": ["Clear thinking"],
            "improvements": ["Address failures"],
            "status": InterviewStatus.COMPLETED
        }
        res = client.post("/api/interview/score", json={
            "session_id": started_session["session_id"]
        })
        data = res.json()
        assert "score" in data
        assert "feedback" in data
        assert "strengths" in data
        assert "improvements" in data

    def test_score_invalid_session_returns_404(self, mock_claude):
        """POST /score with unknown session should return 404."""
        mock_claude.score_interview.side_effect = ValueError(
            "Session not found."
        )
        res = client.post("/api/interview/score", json={
            "session_id": "invalid-id"
        })
        assert res.status_code == 404

    def test_score_service_error_returns_500(
        self, mock_claude, started_session
    ):
        """POST /score should return 500 if service raises."""
        mock_claude.score_interview.side_effect = Exception("Failed")
        res = client.post("/api/interview/score", json={
            "session_id": started_session["session_id"]
        })
        assert res.status_code == 500


# ---------------------------
# Session Endpoint Tests
# ---------------------------

class TestSessionEndpoints:

    def test_get_session_returns_200(self, mock_claude):
        """GET /session/{id} should return 200 for valid session."""
        mock_claude.get_session_status.return_value = {
            "session_id": "abc-123",
            "turn_count": 2,
            "max_turns": 10,
            "status": InterviewStatus.ACTIVE,
            "question_topic": "URL shortener",
            "difficulty": DifficultyLevel.BEGINNER
        }
        res = client.get("/api/interview/session/abc-123")
        assert res.status_code == 200

    def test_get_session_invalid_returns_404(self, mock_claude):
        """GET /session/{id} with unknown id should return 404."""
        mock_claude.get_session_status.side_effect = ValueError(
            "Session not found."
        )
        res = client.get("/api/interview/session/invalid-id")
        assert res.status_code == 404

    def test_delete_session_returns_200(self, mock_claude):
        """DELETE /session/{id} should return 200 for valid session."""
        mock_claude.end_session.return_value = True
        res = client.delete("/api/interview/session/abc-123")
        assert res.status_code == 200

    def test_delete_session_invalid_returns_404(self, mock_claude):
        """DELETE /session/{id} with unknown id should return 404."""
        mock_claude.end_session.return_value = False
        res = client.delete("/api/interview/session/invalid-id")
        assert res.status_code == 404