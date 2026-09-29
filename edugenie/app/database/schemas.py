from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# --- Q&A Schemas ---
class QARequest(BaseModel):
    question: str = Field(..., min_length=2, description="The educational question to ask")
    model_choice: Optional[str] = Field("gemini", description="AI Model to use: 'gemini' or 'lamini'")


class QAResponse(BaseModel):
    query_id: int
    question: str
    answer: str
    model_used: str
    created_at: datetime


# --- Concept Explanation Schemas ---
class ExplainRequest(BaseModel):
    concept: str = Field(..., min_length=2, description="The concept, topic, or theorem to explain")
    model_choice: Optional[str] = Field("gemini", description="AI Model to use: 'gemini' or 'lamini'")


class ExplainResponse(BaseModel):
    query_id: int
    concept: str
    explanation: str
    model_used: str
    created_at: datetime


# --- Quiz Generation Schemas ---
class QuizItem(BaseModel):
    question: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str] = None


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="The topic to generate quiz questions for")
    num_questions: Optional[int] = Field(5, ge=1, le=10, description="Number of questions (1-10)")
    model_choice: Optional[str] = Field("gemini", description="Model to use")


class QuizResponse(BaseModel):
    query_id: int
    topic: str
    questions: List[QuizItem]
    model_used: str
    created_at: datetime


# --- Summarization Schemas ---
class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="The educational text to summarize")
    model_choice: Optional[str] = Field("gemini", description="AI Model to use: 'gemini' or 'lamini'")


class SummarizeResponse(BaseModel):
    query_id: int
    original_text: str
    summary_text: str
    model_used: str
    original_word_count: int
    summary_word_count: int
    created_at: datetime


# --- Learning Path Schemas ---
class LearnRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="The skill, technology, or academic subject")
    level: str = Field("Beginner", description="Level: Beginner, Intermediate, or Advanced")
    model_choice: Optional[str] = Field("gemini", description="AI Model to use")


class LearnResponse(BaseModel):
    query_id: int
    topic: str
    level: str
    learning_path: str
    model_used: str
    created_at: datetime
