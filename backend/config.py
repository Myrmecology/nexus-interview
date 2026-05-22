# ============================================================
# NEXUS INTERVIEW - Configuration
# Loads and validates all environment variables
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # ---------------------------
    # App Settings
    # ---------------------------
    APP_NAME: str = "Nexus Interview"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))

    # ---------------------------
    # Anthropic Settings
    # ---------------------------
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    MAX_TOKENS: int = 1024
    MAX_CONVERSATION_TURNS: int = 10

    # ---------------------------
    # Session Settings
    # ---------------------------
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nexus-dev-secret-key")
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))

    # ---------------------------
    # CORS Settings
    # ---------------------------
    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")

    # ---------------------------
    # Validation
    # ---------------------------
    def validate(self):
        if not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is missing. "
                "Check your .env file."
            )
        return True


settings = Settings()