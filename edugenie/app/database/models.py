import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "USER"

    UserID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserName = Column(String(100), nullable=False)
    Email = Column(String(255), unique=True, nullable=False, index=True)
    PasswordHash = Column(String(255), nullable=False)
    CreatedAt = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    queries = relationship("UserQuery", back_populates="user", cascade="all, delete-orphan")


class UserQuery(Base):
    __tablename__ = "USER_QUERY"

    QueryID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey("USER.UserID"), nullable=True)
    QueryType = Column(String(50), nullable=False)  # 'qa', 'explain', 'quiz', 'summarize', 'learn'
    QueryText = Column(Text, nullable=False)
    CreatedAt = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    user = relationship("User", back_populates="queries")
    ai_responses = relationship("AIResponse", back_populates="query", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPath", back_populates="query", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="query", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="query", cascade="all, delete-orphan")


class AIResponse(Base):
    __tablename__ = "AI_RESPONSE"

    ResponseID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    QueryID = Column(Integer, ForeignKey("USER_QUERY.QueryID"), nullable=False)
    ResponseText = Column(Text, nullable=False)
    ModelUsed = Column(String(100), nullable=False)
    CreatedAt = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    query = relationship("UserQuery", back_populates="ai_responses")


class LearningPath(Base):
    __tablename__ = "LEARNING_PATH"

    PathID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    QueryID = Column(Integer, ForeignKey("USER_QUERY.QueryID"), nullable=False)
    Topic = Column(String(200), nullable=False)
    Level = Column(String(50), nullable=False)  # Beginner, Intermediate, Advanced
    RecommendedTopics = Column(Text, nullable=False)  # JSON or structured markdown
    CreatedAt = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    query = relationship("UserQuery", back_populates="learning_paths")


class Quiz(Base):
    __tablename__ = "QUIZ"

    QuizID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    QueryID = Column(Integer, ForeignKey("USER_QUERY.QueryID"), nullable=False)
    QuestionText = Column(Text, nullable=False)
    OptionA = Column(String(255), nullable=False)
    OptionB = Column(String(255), nullable=False)
    OptionC = Column(String(255), nullable=False)
    OptionD = Column(String(255), nullable=False)
    CorrectOption = Column(String(10), nullable=False)  # "A", "B", "C", or "D"
    CreatedAt = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    query = relationship("UserQuery", back_populates="quizzes")


class Summary(Base):
    __tablename__ = "SUMMARY"

    SummaryID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    QueryID = Column(Integer, ForeignKey("USER_QUERY.QueryID"), nullable=False)
    OriginalText = Column(Text, nullable=False)
    SummaryText = Column(Text, nullable=False)
    ModelUsed = Column(String(100), nullable=False)
    CreatedAt = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    query = relationship("UserQuery", back_populates="summaries")
