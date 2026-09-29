import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Prevent OpenMP issue on Windows during testing
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from app.main import app
from app.database.database import SessionLocal, init_db
from app.database import models

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_db():
    """Ensure database is initialized before running tests."""
    init_db()
    yield


def test_home_page():
    """Test GET / returns 200 and loads HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "EduGenie" in response.text
    assert "Ask Question" in response.text
    assert "Generate Quiz" in response.text


def test_health_endpoint():
    """Test GET /health returns json."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_qa_get_page():
    """Test GET /qa renders Q&A form."""
    response = client.get("/qa")
    assert response.status_code == 200
    assert "Ask Educational Questions" in response.text


@patch("app.services.gemini_service.gemini_service.generate_text")
def test_qa_post_json_success(mock_generate):
    """Test POST /qa with JSON body and mock Gemini response."""
    mock_generate.return_value = "The Pacific Ocean is the largest and deepest ocean on Earth."

    payload = {
        "question": "Which is the largest ocean?",
        "model_choice": "gemini"
    }
    response = client.post("/qa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "Which is the largest ocean?"
    assert "Pacific Ocean" in data["answer"]
    assert data["model_used"] == "Google Gemini"
    assert "query_id" in data

    # Verify record in DB
    db = SessionLocal()
    try:
        saved_query = db.query(models.UserQuery).filter_by(QueryID=data["query_id"]).first()
        assert saved_query is not None
        assert saved_query.QueryType == "qa"
        assert len(saved_query.ai_responses) >= 1
        assert "Pacific" in saved_query.ai_responses[0].ResponseText
    finally:
        db.close()


def test_qa_validation_empty_question():
    """Test POST /qa rejects empty or 1-character questions."""
    response = client.post("/qa", json={"question": " "})
    assert response.status_code == 400
    assert "error" in response.json()


def test_explain_get_page():
    """Test GET /explain renders explanation form."""
    response = client.get("/explain")
    assert response.status_code == 200
    assert "Understand Difficult Concepts" in response.text


@patch("app.services.gemini_service.gemini_service.generate_text")
def test_explain_post_json_success(mock_generate):
    """Test POST /explain with mock response."""
    mock_generate.return_value = (
        "### 1. What It Means\nPythagoras theorem relates the three sides of a right triangle.\n"
        "### 2. Core Rule\na^2 + b^2 = c^2\n"
        "### 3. Real-World Example\nCalculating the height of a ladder against a wall."
    )

    payload = {
        "concept": "Pythagoras theorem",
        "model_choice": "gemini"
    }
    response = client.post("/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["concept"] == "Pythagoras theorem"
    assert "a^2 + b^2 = c^2" in data["explanation"]
    assert "query_id" in data

    # Verify DB
    db = SessionLocal()
    try:
        saved = db.query(models.UserQuery).filter_by(QueryID=data["query_id"]).first()
        assert saved is not None
        assert saved.QueryType == "explain"
    finally:
        db.close()


def test_explain_validation_empty():
    """Test POST /explain rejects blank concept."""
    response = client.post("/explain", json={"concept": " "})
    assert response.status_code == 400


def test_quiz_get_page():
    """Test GET /quiz renders quiz builder."""
    response = client.get("/quiz")
    assert response.status_code == 200
    assert "Generate Interactive Quizzes" in response.text


@patch("app.services.gemini_service.gemini_service.generate_quiz_json")
def test_quiz_post_json_success(mock_quiz_gen):
    """Test POST /quiz generates MCQs and stores questions in QUIZ table."""
    mock_quiz_gen.return_value = [
        {
            "question": "Which keyword is used for loops in Python?",
            "option_a": "for",
            "option_b": "loop",
            "option_c": "repeat",
            "option_d": "iterate",
            "correct_option": "A",
            "explanation": "Python uses 'for' and 'while' keywords for looping."
        },
        {
            "question": "What does range(3) produce?",
            "option_a": "1, 2, 3",
            "option_b": "0, 1, 2",
            "option_c": "0, 1, 2, 3",
            "option_d": "1, 2",
            "correct_option": "B",
            "explanation": "range(n) starts from 0 up to n-1."
        }
    ]

    payload = {
        "topic": "Python loops",
        "num_questions": 2
    }
    response = client.post("/quiz", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Python loops"
    assert len(data["questions"]) == 2
    assert data["questions"][0]["correct_option"] == "A"

    # Verify QUIZ table has records linked to QueryID
    db = SessionLocal()
    try:
        quiz_rows = db.query(models.Quiz).filter_by(QueryID=data["query_id"]).all()
        assert len(quiz_rows) == 2
        assert quiz_rows[0].OptionA == "for"
        assert quiz_rows[0].CorrectOption == "A"
    finally:
        db.close()


def test_quiz_validation_empty_topic():
    """Test POST /quiz validation on empty topic."""
    response = client.post("/quiz", json={"topic": ""})
    assert response.status_code == 400


def test_summarize_get_page():
    """Test GET /summarize renders summarizer."""
    response = client.get("/summarize")
    assert response.status_code == 200
    assert "Summarize Educational Content" in response.text


@patch("app.services.gemini_service.gemini_service.generate_text")
def test_summarize_post_json_success(mock_generate):
    """Test POST /summarize generates concise text and saves in SUMMARY table."""
    mock_generate.return_value = "Photosynthesis is the biological process converting light to chemical energy."

    original_text = (
        "Photosynthesis is a process used by plants and other organisms to convert light energy "
        "into chemical energy that, through cellular respiration, can later be released to fuel the organism's activities."
    )
    payload = {
        "text": original_text,
        "model_choice": "gemini"
    }
    response = client.post("/summarize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Photosynthesis" in data["summary_text"]
    assert data["original_word_count"] > 10

    # Verify SUMMARY entity in SQLite
    db = SessionLocal()
    try:
        summary_record = db.query(models.Summary).filter_by(QueryID=data["query_id"]).first()
        assert summary_record is not None
        assert summary_record.OriginalText == original_text
        assert "Photosynthesis" in summary_record.SummaryText
    finally:
        db.close()


def test_summarize_validation_too_short():
    """Test POST /summarize rejects very short texts."""
    response = client.post("/summarize", json={"text": "Short"})
    assert response.status_code == 400


def test_learn_get_page():
    """Test GET /learn renders roadmap view."""
    response = client.get("/learn")
    assert response.status_code == 200
    assert "Personalized Learning Path" in response.text


@patch("app.services.gemini_service.gemini_service.generate_text")
def test_learn_post_json_success(mock_generate):
    """Test POST /learn generates curriculum and stores in LEARNING_PATH table."""
    mock_generate.return_value = (
        "## Target Goal: Master SQL\n"
        "## Step-by-Step Curriculum\n"
        "1. SQL basics\n2. SELECT\n3. WHERE\n4. ORDER BY\n5. GROUP BY\n"
        "## Recommendations: Practice queries on SQLite."
    )

    payload = {
        "topic": "SQL",
        "level": "Beginner"
    }
    response = client.post("/learn", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "SQL"
    assert data["level"] == "Beginner"
    assert "SQL basics" in data["learning_path"]

    # Verify LEARNING_PATH record
    db = SessionLocal()
    try:
        lp = db.query(models.LearningPath).filter_by(QueryID=data["query_id"]).first()
        assert lp is not None
        assert lp.Topic == "SQL"
        assert lp.Level == "Beginner"
    finally:
        db.close()


def test_learn_validation_empty_topic():
    """Test POST /learn rejects empty topic."""
    response = client.post("/learn", json={"topic": ""})
    assert response.status_code == 400
