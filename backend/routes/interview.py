# ============================================================
# NEXUS INTERVIEW - Interview Routes
# All API endpoints for the interview experience
# ============================================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models.schemas import (
    StartInterviewRequest,
    StartInterviewResponse,
    ChatRequest,
    ChatResponse,
    HintRequest,
    HintResponse,
    ScoreResponse,
    InterviewStatus
)
from backend.services.claude_service import claude_service
from backend.config import settings

router = APIRouter(prefix="/api/interview", tags=["Interview"])


# ---------------------------
# Health Check
# ---------------------------

@router.get("/health")
def health_check():
    """Confirms the interview service is running."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# ---------------------------
# Start Interview
# ---------------------------

@router.post("/start", response_model=StartInterviewResponse)
def start_interview(request: StartInterviewRequest):
    """
    Creates a new interview session.
    Returns session ID and opening message from Nexus.
    """
    try:
        result = claude_service.start_interview(
            difficulty=request.difficulty,
            topic=request.topic
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}"
        )


# ---------------------------
# Chat — Streaming
# ---------------------------

@router.post("/chat")
def chat(request: ChatRequest):
    """
    Sends a message to Nexus and streams
    the response back word by word in real time.
    """
    try:
        def generate():
            for chunk in claude_service.stream_chat(
                session_id=request.session_id,
                user_message=request.message
            ):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="text/plain"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


# ---------------------------
# Get Hint
# ---------------------------

@router.post("/hint", response_model=HintResponse)
def get_hint(request: HintRequest):
    """
    Returns a single nudge hint to the candidate
    without giving the full answer away.
    """
    try:
        hint = claude_service.get_hint(
            session_id=request.session_id
        )
        return {
            "session_id": request.session_id,
            "hint": hint
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get hint: {str(e)}"
        )


# ---------------------------
# Score Interview
# ---------------------------

@router.post("/score", response_model=ScoreResponse)
def score_interview(request: HintRequest):
    """
    Reviews the full conversation and returns
    a structured score with detailed feedback.
    """
    try:
        result = claude_service.score_interview(
            session_id=request.session_id
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}"
        )


# ---------------------------
# Session Status
# ---------------------------

@router.get("/session/{session_id}")
def get_session(session_id: str):
    """
    Returns current session metadata —
    turn count, status, and topic.
    """
    try:
        return claude_service.get_session_status(
            session_id=session_id
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


# ---------------------------
# End Session
# ---------------------------

@router.delete("/session/{session_id}")
def end_session(session_id: str):
    """
    Manually ends and cleans up a session.
    """
    try:
        success = claude_service.end_session(
            session_id=session_id
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Session not found."
            )
        return {
            "status": "success",
            "message": "Session ended.",
            "session_id": session_id
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end session: {str(e)}"
        )