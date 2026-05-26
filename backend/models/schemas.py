# ============================================================
# NEXUS INTERVIEW - Pydantic Schemas
# Defines all request and response data models
# ============================================================

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from enum import Enum


# ---------------------------
# Enums
# ---------------------------

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class InterviewStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# ---------------------------
# Interview Request Models
# ---------------------------

class StartInterviewRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "difficulty": "beginner",
                "topic": "url shortener"
            }
        }
    )

    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.BEGINNER,
        description="Difficulty level of the interview"
    )
    topic: Optional[str] = Field(
        default=None,
        description="Optional specific topic to focus on"
    )


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "abc-123",
                "message": "I would start with an API gateway..."
            }
        }
    )

    session_id: str = Field(
        description="Unique session identifier"
    )
    message: str = Field(
        description="User message to the interviewer",
        min_length=1,
        max_length=5000
    )


class HintRequest(BaseModel):
    session_id: str = Field(
        description="Unique session identifier"
    )


# ---------------------------
# Interview Response Models
# ---------------------------

class StartInterviewResponse(BaseModel):
    session_id: str
    message: str
    difficulty: DifficultyLevel
    question_topic: str
    turn_count: int = 0
    max_turns: int = 10
    status: InterviewStatus = InterviewStatus.ACTIVE


class ChatResponse(BaseModel):
    session_id: str
    message: str
    turn_count: int
    max_turns: int
    status: InterviewStatus
    is_scored: bool = False


class ScoreBreakdown(BaseModel):
    scalability: int = Field(ge=0, le=10)
    reliability: int = Field(ge=0, le=10)
    communication: int = Field(ge=0, le=10)
    overall: int = Field(ge=0, le=10)


class ScoreResponse(BaseModel):
    session_id: str
    score: ScoreBreakdown
    feedback: str
    strengths: list[str]
    improvements: list[str]
    status: InterviewStatus = InterviewStatus.COMPLETED


class HintResponse(BaseModel):
    session_id: str
    hint: str


# ---------------------------
# Health Check
# ---------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str