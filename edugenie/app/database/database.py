import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Ensure the data directory exists
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "edugenie.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# SQLite configuration (check_same_thread=False for FastAPI concurrency)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes tables and seeds a default guest user if needed."""
    from . import models
    Base.metadata.create_all(bind=engine)

    # Seed default guest user for non-authenticated sessions
    db = SessionLocal()
    try:
        guest = db.query(models.User).filter_by(UserName="guest_student").first()
        if not guest:
            guest = models.User(
                UserName="guest_student",
                Email="student@edugenie.local",
                PasswordHash="guest_placeholder_hash"
            )
            db.add(guest)
            db.commit()
    finally:
        db.close()
