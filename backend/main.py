# ============================================================
# NEXUS INTERVIEW - Main Application Entry Point
# Ties the entire backend together
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.routes.interview import router as interview_router


# ---------------------------
# App Initialization
# ---------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered System Design Interview Simulator",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ---------------------------
# CORS Middleware
# ---------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ---------------------------
# Validate Settings on Startup
# ---------------------------

@app.on_event("startup")
async def startup_event():
    """
    Runs on app startup.
    Validates all required environment variables
    before accepting any requests.
    """
    try:
        settings.validate()
        print(f"✅ {settings.APP_NAME} v{settings.APP_VERSION} is running")
        print(f"✅ Claude model: {settings.CLAUDE_MODEL}")
        print(f"✅ Docs available at: http://{settings.HOST}:{settings.PORT}/docs")
    except ValueError as e:
        print(f"❌ Startup failed: {e}")
        raise


# ---------------------------
# Register Routes
# ---------------------------

app.include_router(interview_router)


# ---------------------------
# Serve Frontend
# ---------------------------

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)


@app.get("/", include_in_schema=False)
def serve_frontend():
    """Serves the main frontend HTML file."""
    return FileResponse("frontend/index.html")


# ---------------------------
# Run Application
# ---------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )