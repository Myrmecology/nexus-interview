# ============================================================
# NEXUS INTERVIEW - Claude Service
# The AI brain — handles all communication with Claude API
# ============================================================

import uuid
import anthropic
from backend.config import settings
from backend.models.schemas import (
    DifficultyLevel,
    InterviewStatus,
    ScoreBreakdown
)


# ---------------------------
# Interview Questions Bank
# ---------------------------

QUESTIONS = {
    DifficultyLevel.BEGINNER: [
        "Design a URL shortener like Bit.ly",
        "Design a rate limiter",
        "Design a parking lot system",
        "Design a simple cache system",
    ],
    DifficultyLevel.INTERMEDIATE: [
        "Design a notification system like push alerts",
        "Design a ride sharing service like Uber",
        "Design a social media news feed",
        "Design a chat messaging system like WhatsApp",
    ],
    DifficultyLevel.ADVANCED: [
        "Design YouTube's video upload pipeline",
        "Design Twitter's trending topics system",
        "Design a distributed job scheduler",
        "Design a global content delivery network",
    ]
}


# ---------------------------
# System Prompts
# ---------------------------

INTERVIEWER_SYSTEM_PROMPT = """
You are Nexus, a senior staff engineer at a top-tier tech company 
conducting a system design interview. Your personality is sharp, 
professional, and direct — like a real FAANG interviewer.

Your rules:
- Start with ONE clear system design challenge
- Listen carefully to the candidate's answer
- Ask ONE pointed follow-up question at a time
- Probe weak spots in their architecture relentlessly
- Never give the answer away — only guide with questions
- Be concise — real interviewers don't write essays
- After {max_turns} total exchanges, tell the candidate 
  time is up and that scoring is complete

Your tone:
- Professional but not warm
- Challenging but fair
- Direct and specific — never vague

Remember: You are evaluating their ability to think at scale.
"""

HINT_SYSTEM_PROMPT = """
You are Nexus, a system design interview coach.
The candidate is stuck and needs a nudge — not the answer.
Give ONE short, specific hint that points them in the right 
direction without solving the problem for them.
Keep it under 3 sentences. Be direct.
"""

SCORING_SYSTEM_PROMPT = """
You are Nexus, a senior staff engineer scoring a system design interview.
Review the entire conversation and score the candidate.

You MUST respond in this exact JSON format and nothing else:
{
    "scalability": <score 0-10>,
    "reliability": <score 0-10>,
    "communication": <score 0-10>,
    "overall": <score 0-10>,
    "feedback": "<2-3 sentence overall summary>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "improvements": ["<improvement 1>", "<improvement 2>"]
}

Scoring criteria:
- Scalability: Did they think about load, traffic, and growth?
- Reliability: Did they address failures, retries, and redundancy?
- Communication: Were they clear, structured, and logical?
- Overall: Holistic impression of their engineering thinking
"""


# ---------------------------
# Session Storage
# ---------------------------

# In-memory session store
# Stores conversation history per session
sessions: dict = {}


# ---------------------------
# Claude Service Class
# ---------------------------

class ClaudeService:

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

    # ---------------------------
    # Start Interview
    # ---------------------------

    def start_interview(
        self,
        difficulty: DifficultyLevel,
        topic: str = None
    ) -> dict:
        """
        Creates a new interview session and returns
        the opening message from the interviewer.
        """
        import random

        # Generate unique session
        session_id = str(uuid.uuid4())

        # Pick question
        if topic:
            question_topic = topic
        else:
            question_topic = random.choice(QUESTIONS[difficulty])

        # Build opening prompt
        opening_prompt = (
            f"Start the interview. "
            f"The challenge is: {question_topic}. "
            f"Greet the candidate briefly and present the challenge. "
            f"Keep it under 4 sentences."
        )

        # Format system prompt
        system = INTERVIEWER_SYSTEM_PROMPT.format(
            max_turns=settings.MAX_CONVERSATION_TURNS
        )

        # Call Claude
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.MAX_TOKENS,
            system=system,
            messages=[
                {"role": "user", "content": opening_prompt}
            ]
        )

        opening_message = response.content[0].text

        # Store session
        sessions[session_id] = {
            "difficulty": difficulty,
            "question_topic": question_topic,
            "status": InterviewStatus.ACTIVE,
            "turn_count": 0,
            "history": [
                {"role": "user", "content": opening_prompt},
                {"role": "assistant", "content": opening_message}
            ]
        }

        return {
            "session_id": session_id,
            "message": opening_message,
            "difficulty": difficulty,
            "question_topic": question_topic,
            "turn_count": 0,
            "max_turns": settings.MAX_CONVERSATION_TURNS,
            "status": InterviewStatus.ACTIVE
        }

    # ---------------------------
    # Chat — Streaming Response
    # ---------------------------

    def stream_chat(self, session_id: str, user_message: str):
        """
        Streams Claude's response word by word.
        Yields text chunks as they arrive.
        """
        if session_id not in sessions:
            raise ValueError("Session not found.")

        session = sessions[session_id]

        if session["status"] != InterviewStatus.ACTIVE:
            raise ValueError("Interview is no longer active.")

        # Append user message to history
        session["history"].append(
            {"role": "user", "content": user_message}
        )

        # Format system prompt
        system = INTERVIEWER_SYSTEM_PROMPT.format(
            max_turns=settings.MAX_CONVERSATION_TURNS
        )

        # Stream from Claude
        full_response = ""

        with self.client.messages.stream(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.MAX_TOKENS,
            system=system,
            messages=session["history"]
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield text

        # Save assistant response to history
        session["history"].append(
            {"role": "assistant", "content": full_response}
        )

        # Increment turn count
        session["turn_count"] += 1

        # Auto-complete if max turns reached
        if session["turn_count"] >= settings.MAX_CONVERSATION_TURNS:
            session["status"] = InterviewStatus.COMPLETED

    # ---------------------------
    # Get Hint
    # ---------------------------

    def get_hint(self, session_id: str) -> str:
        """
        Returns a single nudge hint without
        giving the full answer away.
        """
        if session_id not in sessions:
            raise ValueError("Session not found.")

        session = sessions[session_id]

        # Summarize conversation for hint context
        context = f"""
        The candidate is designing: {session['question_topic']}.
        Here is the conversation so far:
        {session['history']}
        Give them one helpful nudge.
        """

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=300,
            system=HINT_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": context}
            ]
        )

        return response.content[0].text

    # ---------------------------
    # Score Interview
    # ---------------------------

    def score_interview(self, session_id: str) -> dict:
        """
        Reviews the full conversation and returns
        a structured score with feedback.
        """
        import json

        if session_id not in sessions:
            raise ValueError("Session not found.")

        session = sessions[session_id]

        # Build scoring context
        context = f"""
        System design challenge: {session['question_topic']}
        Difficulty: {session['difficulty']}
        
        Full interview transcript:
        {session['history']}
        
        Score this candidate now.
        """

        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=800,
            system=SCORING_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": context}
            ]
        )

        # Parse JSON score
        raw = response.content[0].text.strip()
        score_data = json.loads(raw)

        # Mark session complete
        session["status"] = InterviewStatus.COMPLETED

        return {
            "session_id": session_id,
            "score": ScoreBreakdown(
                scalability=score_data["scalability"],
                reliability=score_data["reliability"],
                communication=score_data["communication"],
                overall=score_data["overall"]
            ),
            "feedback": score_data["feedback"],
            "strengths": score_data["strengths"],
            "improvements": score_data["improvements"],
            "status": InterviewStatus.COMPLETED
        }

    # ---------------------------
    # Session Helpers
    # ---------------------------

    def get_session_status(self, session_id: str) -> dict:
        """Returns current session metadata."""
        if session_id not in sessions:
            raise ValueError("Session not found.")

        session = sessions[session_id]

        return {
            "session_id": session_id,
            "turn_count": session["turn_count"],
            "max_turns": settings.MAX_CONVERSATION_TURNS,
            "status": session["status"],
            "question_topic": session["question_topic"],
            "difficulty": session["difficulty"]
        }

    def end_session(self, session_id: str) -> bool:
        """Manually ends and cleans up a session."""
        if session_id in sessions:
            sessions[session_id]["status"] = InterviewStatus.ABANDONED
            return True
        return False


# ---------------------------
# Singleton Instance
# ---------------------------

claude_service = ClaudeService()