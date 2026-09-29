import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("edugenie")

from .database.database import init_db, get_db
from .database import models
from .routers import qa, explain, quiz, summarize, learn
from .services.gemini_service import gemini_service
from .services.laminiflant5_service import lamini_service

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events."""
    logger.info("Starting up EduGenie...")
    init_db()
    logger.info("Database initialized successfully.")
    yield
    logger.info("Shutting down EduGenie...")


app = FastAPI(
    title="EduGenie – Google Gemini Powered Learning Assistant",
    description="A lightweight AI-powered educational assistant for students, self-learners, and educators.",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static assets
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Template engine
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(qa.router)
app.include_router(explain.router)
app.include_router(quiz.router)
app.include_router(summarize.router)
app.include_router(learn.router)


@app.get("/", response_class=HTMLResponse)
def get_home_page(request: Request, db: Session = Depends(get_db)):
    """Home dashboard featuring EduGenie's 5 core capabilities, stats, and quick links."""
    total_queries = db.query(models.UserQuery).count()
    total_quizzes = db.query(models.Quiz).count()
    total_summaries = db.query(models.Summary).count()
    total_paths = db.query(models.LearningPath).count()

    recent_activity = (
        db.query(models.UserQuery)
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(6)
        .all()
    )

    gemini_ready = gemini_service.is_available()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "page_title": "EduGenie – AI-Powered Learning Assistant",
            "total_queries": total_queries,
            "total_quizzes": total_quizzes,
            "total_summaries": total_summaries,
            "total_paths": total_paths,
            "recent_activity": recent_activity,
            "gemini_ready": gemini_ready,
            "lamini_status": lamini_service.get_status()
        }
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gemini_available": gemini_service.is_available(),
        "lamini_loaded": lamini_service.is_loaded()
    }


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={
            "page_title": "Page Not Found - EduGenie",
            "error": "The requested page or resource could not be found."
        },
        status_code=404
    )
