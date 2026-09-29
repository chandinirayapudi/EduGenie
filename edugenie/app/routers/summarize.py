import logging
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from ..database.database import get_db
from ..database import models
from ..prompts.prompts import get_summarize_prompt
from ..services.gemini_service import gemini_service
from ..services.laminiflant5_service import lamini_service

logger = logging.getLogger("edugenie.routers.summarize")
router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _process_summarize(text: str, model_choice: str, db: Session):
    clean_text = text.strip()
    if len(clean_text) < 10:
        raise ValueError("Please provide at least 10 characters of educational text to summarize.")

    prompt = get_summarize_prompt(clean_text)
    model_choice = model_choice.lower()

    if model_choice in ["lamini", "local", "laminiflant5"]:
        try:
            summary = lamini_service.generate_text(prompt, max_length=200, min_length=25)
            model_used = "LaMini-Flan-T5"
        except Exception as e:
            logger.warning(f"LaMini-Flan-T5 failed, falling back to Gemini: {e}")
            summary = gemini_service.generate_text(prompt)
            model_used = "Gemini (Fallback from LaMini)"
    else:
        summary = gemini_service.generate_text(prompt)
        model_used = "Google Gemini"

    orig_word_count = len(clean_text.split())
    summary_word_count = len(summary.split())

    # Persist in SQLite
    guest_user = db.query(models.User).filter_by(UserName="guest_student").first()
    user_id = guest_user.UserID if guest_user else None

    # Truncate preview for query text if very long
    preview_query = (clean_text[:120] + "...") if len(clean_text) > 120 else clean_text
    query_record = models.UserQuery(
        UserID=user_id,
        QueryType="summarize",
        QueryText=f"Summarize text: {preview_query}"
    )
    db.add(query_record)
    db.flush()

    summary_record = models.Summary(
        QueryID=query_record.QueryID,
        OriginalText=clean_text,
        SummaryText=summary,
        ModelUsed=model_used
    )
    db.add(summary_record)

    response_record = models.AIResponse(
        QueryID=query_record.QueryID,
        ResponseText=summary,
        ModelUsed=model_used
    )
    db.add(response_record)

    db.commit()
    db.refresh(query_record)
    db.refresh(summary_record)

    return {
        "query_id": query_record.QueryID,
        "original_text": clean_text,
        "summary_text": summary,
        "model_used": model_used,
        "original_word_count": orig_word_count,
        "summary_word_count": summary_word_count,
        "created_at": summary_record.CreatedAt
    }


@router.get("/summarize", response_class=HTMLResponse)
def get_summarize_page(request: Request, db: Session = Depends(get_db)):
    recent_summaries = (
        db.query(models.Summary)
        .order_by(models.Summary.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="summarize.html",
        context={
            "page_title": "EduGenie - Text Summarizer",
            "recent_summaries": recent_summaries
        }
    )


@router.post("/summarize")
async def post_summarize(
    request: Request,
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        try:
            body = await request.json()
            text = body.get("text", "")
            model_choice = body.get("model_choice", "gemini")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        form = await request.form()
        text = form.get("text", "")
        model_choice = form.get("model_choice", "gemini")

    try:
        result = _process_summarize(text=text, model_choice=model_choice, db=db)
    except ValueError as ve:
        if is_json:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        return templates.TemplateResponse(
            request=request,
            name="summarize.html",
            context={
                "error": str(ve),
                "text": text,
                "model_choice": model_choice
            }
        )
    except Exception as e:
        logger.error(f"Error in /summarize: {e}")
        err_msg = str(e)
        if is_json:
            return JSONResponse(status_code=500, content={"error": err_msg})
        return templates.TemplateResponse(
            request=request,
            name="summarize.html",
            context={
                "error": err_msg,
                "text": text,
                "model_choice": model_choice
            }
        )

    if is_json:
        return JSONResponse(content={
            "query_id": result["query_id"],
            "original_text": result["original_text"],
            "summary_text": result["summary_text"],
            "model_used": result["model_used"],
            "original_word_count": result["original_word_count"],
            "summary_word_count": result["summary_word_count"],
            "created_at": result["created_at"].isoformat()
        })

    recent_summaries = (
        db.query(models.Summary)
        .order_by(models.Summary.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="summarize.html",
        context={
            "result": result,
            "text": text,
            "model_choice": model_choice,
            "recent_summaries": recent_summaries
        }
    )
