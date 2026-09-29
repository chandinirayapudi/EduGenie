import logging
from fastapi import APIRouter, Depends, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from ..database.database import get_db
from ..database import models
from ..prompts.prompts import get_explain_prompt
from ..services.gemini_service import gemini_service
from ..services.laminiflant5_service import lamini_service

logger = logging.getLogger("edugenie.routers.explain")
router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _process_explain(concept: str, model_choice: str, db: Session):
    clean_concept = concept.strip()
    if len(clean_concept) < 2:
        raise ValueError("Please enter a valid concept or topic name (at least 2 characters).")

    prompt = get_explain_prompt(clean_concept)
    model_choice = model_choice.lower()

    if model_choice in ["lamini", "local", "laminiflant5"]:
        try:
            explanation = lamini_service.generate_text(prompt, max_length=350)
            model_used = "LaMini-Flan-T5"
        except Exception as e:
            logger.warning(f"LaMini-Flan-T5 failed, falling back to Gemini: {e}")
            explanation = gemini_service.generate_text(prompt)
            model_used = "Gemini (Fallback from LaMini)"
    else:
        explanation = gemini_service.generate_text(prompt)
        model_used = "Google Gemini"

    # Persist in SQLite
    guest_user = db.query(models.User).filter_by(UserName="guest_student").first()
    user_id = guest_user.UserID if guest_user else None

    query_record = models.UserQuery(
        UserID=user_id,
        QueryType="explain",
        QueryText=clean_concept
    )
    db.add(query_record)
    db.flush()

    response_record = models.AIResponse(
        QueryID=query_record.QueryID,
        ResponseText=explanation,
        ModelUsed=model_used
    )
    db.add(response_record)
    db.commit()
    db.refresh(query_record)
    db.refresh(response_record)

    return {
        "query_id": query_record.QueryID,
        "concept": clean_concept,
        "explanation": explanation,
        "model_used": model_used,
        "created_at": response_record.CreatedAt
    }


@router.get("/explain", response_class=HTMLResponse)
def get_explain_page(request: Request, db: Session = Depends(get_db)):
    recent_queries = (
        db.query(models.UserQuery)
        .filter_by(QueryType="explain")
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="explain.html",
        context={
            "page_title": "EduGenie - Concept Explainer",
            "recent_queries": recent_queries
        }
    )


@router.post("/explain")
async def post_explain(
    request: Request,
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        try:
            body = await request.json()
            concept = body.get("concept", "")
            model_choice = body.get("model_choice", "gemini")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")
    else:
        form = await request.form()
        concept = form.get("concept", "")
        model_choice = form.get("model_choice", "gemini")

    try:
        result = _process_explain(concept=concept, model_choice=model_choice, db=db)
    except ValueError as ve:
        if is_json:
            return JSONResponse(status_code=400, content={"error": str(ve)})
        return templates.TemplateResponse(
            request=request,
            name="explain.html",
            context={
                "error": str(ve),
                "concept": concept,
                "model_choice": model_choice
            }
        )
    except Exception as e:
        logger.error(f"Error in /explain: {e}")
        err_msg = str(e)
        if is_json:
            return JSONResponse(status_code=500, content={"error": err_msg})
        return templates.TemplateResponse(
            request=request,
            name="explain.html",
            context={
                "error": err_msg,
                "concept": concept,
                "model_choice": model_choice
            }
        )

    if is_json:
        return JSONResponse(content={
            "query_id": result["query_id"],
            "concept": result["concept"],
            "explanation": result["explanation"],
            "model_used": result["model_used"],
            "created_at": result["created_at"].isoformat()
        })

    recent_queries = (
        db.query(models.UserQuery)
        .filter_by(QueryType="explain")
        .order_by(models.UserQuery.CreatedAt.desc())
        .limit(5)
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="explain.html",
        context={
            "result": result,
            "concept": concept,
            "model_choice": model_choice,
            "recent_queries": recent_queries
        }
    )
