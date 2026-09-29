import json
import logging
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from ..database.database import get_db
from ..database import models
from ..prompts.prompts import get_quiz_prompt
from ..services.gemini_service import gemini_service

logger = logging.getLogger("edugenie.routers.quiz")
router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _process_quiz(topic: str, num_questions: int, db: Session):
    clean_topic = topic.strip()
    if len(clean_topic) < 2:
        raise ValueError("Please enter a valid topic for the quiz (at least 2 characters).")

    if num_questions < 1 or num_questions > 10:
        num_questions = 5

    prompt = get_quiz_prompt(clean_topic, num_questions)
    questions = gemini_service.generate_quiz_json(prompt, num_questions)
    model_used = "Google Gemini"

    # Persist in SQLite
    guest_user = db.query(models.User).filter_by(UserName="guest_student").first()
    user_id = guest_user.UserID if guest_user else None

    query_record = models.UserQuery(
        UserID=user_id,
        QueryType="quiz",
        QueryText=f"Quiz Topic: {clean_topic} ({num_questions} questions)"
    )
    db.add(query_record)
    db.flush()

    # Store each generated question in the QUIZ table connected to the same QueryID
    quiz_records = []
    for q in questions:
        quiz_item = models.Quiz(
            QueryID=query_record.QueryID,
            QuestionText=q["question"],
            OptionA=q["option_a"],
            OptionB=q["option_b"],
            OptionC=q["option_c"],
            OptionD=q["option_d"],
            CorrectOption=q["correct_option"]
        )
        db.add(quiz_item)
        quiz_records.append(quiz_item)

    # Also record summary in AI_RESPONSE
    response_record = models.AIResponse(
        QueryID=query_record.QueryID,
        ResponseText=json.dumps(questions),
        ModelUsed=model_used
    )
    db.add(response_record)

    db.commit()
    db.refresh(query_record)

    return {
        "query_id": query_record.QueryID,
        "topic": clean_topic,
        "questions": questions,
        "model_used": model_used,
        "created_at": query_record.CreatedAt
    }


@router.get("/quiz", response_class=HTMLResponse)
def get_quiz_page(request: Request, db: Session = Depends(get_db)):
    recent_quizzes = (
        db.query(models.UserQuery)
        .filter_by(QueryType="quiz")
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="quiz.html",
        context={
            "page_title": "EduGenie - Interactive Quiz Generator",
            "recent_quizzes": recent_quizzes
        }
    )


@router.post("/quiz")
async def post_quiz(
    request: Request,
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        try:
            body = await request.json()
            topic = body.get("topic", "")
            num_questions = int(body.get("num_questions", 5))
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        form = await request.form()
        topic = form.get("topic", "")
        try:
            num_questions = int(form.get("num_questions", 5))
        except (TypeError, ValueError):
            num_questions = 5

    try:
        result = _process_quiz(topic=topic, num_questions=num_questions, db=db)
    except ValueError as ve:
        if is_json:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        return templates.TemplateResponse(
            request=request,
            name="quiz.html",
            context={
                "error": str(ve),
                "topic": topic,
                "num_questions": num_questions
            }
        )
    except Exception as e:
        logger.error(f"Error in /quiz: {e}")
        err_msg = str(e)
        if is_json:
            return JSONResponse(status_code=500, content={"error": err_msg})
        return templates.TemplateResponse(
            request=request,
            name="quiz.html",
            context={
                "error": err_msg,
                "topic": topic,
                "num_questions": num_questions
            }
        )

    if is_json:
        return JSONResponse(content={
            "query_id": result["query_id"],
            "topic": result["topic"],
            "questions": result["questions"],
            "model_used": result["model_used"],
            "created_at": result["created_at"].isoformat()
        })

    recent_quizzes = (
        db.query(models.UserQuery)
        .filter_by(QueryType="quiz")
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="quiz.html",
        context={
            "result": result,
            "topic": topic,
            "num_questions": num_questions,
            "recent_quizzes": recent_quizzes
        }
    )
