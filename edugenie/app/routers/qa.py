import logging
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from ..database.database import get_db
from ..database import models
from ..database.schemas import QARequest, QAResponse
from ..prompts.prompts import get_qa_prompt
from ..services.gemini_service import gemini_service
from ..services.laminiflant5_service import lamini_service

logger = logging.getLogger("edugenie.routers.qa")
router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _process_qa(question: str, model_choice: str, db: Session):
    clean_question = question.strip()
    if len(clean_question) < 2:
        raise ValueError("Please provide a valid question (at least 2 characters).")

    # Generate answer using selected model
    prompt = get_qa_prompt(clean_question)
    model_choice = model_choice.lower()

    if model_choice in ["lamini", "local", "laminiflant5"]:
        try:
            answer = lamini_service.generate_text(prompt, max_length=256)
            model_used = "LaMini-Flan-T5"
        except Exception as e:
            logger.warning(f"LaMini-Flan-T5 failed, falling back to Gemini: {e}")
            answer = gemini_service.generate_text(prompt)
            model_used = "Gemini (Fallback from LaMini)"
    else:
        answer = gemini_service.generate_text(prompt)
        model_used = "Google Gemini"

    # Persist in SQLite
    guest_user = db.query(models.User).filter_by(UserName="guest_student").first()
    user_id = guest_user.UserID if guest_user else None

    query_record = models.UserQuery(
        UserID=user_id,
        QueryType="qa",
        QueryText=clean_question
    )
    db.add(query_record)
    db.flush()

    response_record = models.AIResponse(
        QueryID=query_record.QueryID,
        ResponseText=answer,
        ModelUsed=model_used
    )
    db.add(response_record)
    db.commit()
    db.refresh(query_record)
    db.refresh(response_record)

    return {
        "query_id": query_record.QueryID,
        "question": clean_question,
        "answer": answer,
        "model_used": model_used,
        "created_at": response_record.CreatedAt
    }


@router.get("/qa", response_class=HTMLResponse)
def get_qa_page(request: Request, db: Session = Depends(get_db)):
    # Fetch recent Q&A history
    recent_queries = (
        db.query(models.UserQuery)
        .filter_by(QueryType="qa")
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="qa.html",
        context={
            "page_title": "EduGenie - Educational Q&A",
            "recent_queries": recent_queries
        }
    )


@router.post("/qa")
async def post_qa(
    request: Request,
    db: Session = Depends(get_db)
):
    # Check if request is JSON or Form data
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        try:
            body = await request.json()
            question = body.get("question", "")
            model_choice = body.get("model_choice", "gemini")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        form = await request.form()
        question = form.get("question", "")
        model_choice = form.get("model_choice", "gemini")

    try:
        result = _process_qa(question=question, model_choice=model_choice, db=db)
    except ValueError as ve:
        if is_json:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        return templates.TemplateResponse(
            request=request,
            name="qa.html",
            context={
                "error": str(ve),
                "question": question,
                "model_choice": model_choice
            }
        )
    except Exception as e:
        logger.error(f"Error in /qa: {e}")
        err_msg = str(e)
        if is_json:
            return JSONResponse(status_code=500, content={"error": err_msg})
        return templates.TemplateResponse(
            request=request,
            name="qa.html",
            context={
                "error": err_msg,
                "question": question,
                "model_choice": model_choice
            }
        )

    if is_json:
        return JSONResponse(content={
            "query_id": result["query_id"],
            "question": result["question"],
            "answer": result["answer"],
            "model_used": result["model_used"],
            "created_at": result["created_at"].isoformat()
        })

    # Render template for standard form submission
    recent_queries = (
        db.query(models.UserQuery)
        .filter_by(QueryType="qa")
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="qa.html",
        context={
            "result": result,
            "question": question,
            "model_choice": model_choice,
            "recent_queries": recent_queries
        }
    )
