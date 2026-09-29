import logging
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from ..database.database import get_db
from ..database import models
from ..prompts.prompts import get_learning_path_prompt
from ..services.gemini_service import gemini_service

logger = logging.getLogger("edugenie.routers.learn")
router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

VALID_LEVELS = ["Beginner", "Intermediate", "Advanced"]


def _process_learn(topic: str, level: str, db: Session):
    clean_topic = topic.strip()
    if len(clean_topic) < 2:
        raise ValueError("Please provide a valid subject or topic (at least 2 characters).")

    # Capitalize level correctly
    norm_level = level.strip().capitalize()
    if norm_level not in VALID_LEVELS:
        norm_level = "Beginner"

    prompt = get_learning_path_prompt(clean_topic, norm_level)
    path_text = gemini_service.generate_text(prompt)
    model_used = "Google Gemini"

    # Persist in SQLite
    guest_user = db.query(models.User).filter_by(UserName="guest_student").first()
    user_id = guest_user.UserID if guest_user else None

    query_record = models.UserQuery(
        UserID=user_id,
        QueryType="learn",
        QueryText=f"Learning Path: {clean_topic} ({norm_level})"
    )
    db.add(query_record)
    db.flush()

    learning_path_record = models.LearningPath(
        QueryID=query_record.QueryID,
        Topic=clean_topic,
        Level=norm_level,
        RecommendedTopics=path_text
    )
    db.add(learning_path_record)

    response_record = models.AIResponse(
        QueryID=query_record.QueryID,
        ResponseText=path_text,
        ModelUsed=model_used
    )
    db.add(response_record)

    db.commit()
    db.refresh(query_record)
    db.refresh(learning_path_record)

    return {
        "query_id": query_record.QueryID,
        "topic": clean_topic,
        "level": norm_level,
        "learning_path": path_text,
        "model_used": model_used,
        "created_at": learning_path_record.CreatedAt
    }


@router.get("/learn", response_class=HTMLResponse)
def get_learn_page(request: Request, db: Session = Depends(get_db)):
    recent_paths = (
        db.query(models.LearningPath)
        .order_by(models.LearningPath.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="learn.html",
        context={
            "page_title": "EduGenie - Learning Path & Recommendations",
            "recent_paths": recent_paths
        }
    )


@router.post("/learn")
async def post_learn(
    request: Request,
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        try:
            body = await request.json()
            topic = body.get("topic", "")
            level = body.get("level", "Beginner")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        form = await request.form()
        topic = form.get("topic", "")
        level = form.get("level", "Beginner")

    try:
        result = _process_learn(topic=topic, level=level, db=db)
    except ValueError as ve:
        if is_json:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        return templates.TemplateResponse(
            request=request,
            name="learn.html",
            context={
                "error": str(ve),
                "topic": topic,
                "level": level
            }
        )
    except Exception as e:
        logger.error(f"Error in /learn: {e}")
        err_msg = str(e)
        if is_json:
            return JSONResponse(status_code=500, content={"error": err_msg})
        return templates.TemplateResponse(
            request=request,
            name="learn.html",
            context={
                "error": err_msg,
                "topic": topic,
                "level": level
            }
        )

    if is_json:
        return JSONResponse(content={
            "query_id": result["query_id"],
            "topic": result["topic"],
            "level": result["level"],
            "learning_path": result["learning_path"],
            "model_used": result["model_used"],
            "created_at": result["created_at"].isoformat()
        })

    recent_paths = (
        db.query(models.LearningPath)
        .order_by(models.LearningPath.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="learn.html",
        context={
            "result": result,
            "topic": topic,
            "level": level,
            "recent_paths": recent_paths
        }
    )
