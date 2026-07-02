import os
import sqlite3
import string

from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))


def _resolve_db_path() -> str:
    candidates = [
        os.path.join(PROJECT_ROOT, "users.db"),
        os.path.join(BASE_DIR, "users.db"),
    ]

    for candidate in candidates:
        if not os.path.exists(candidate):
            continue
        try:
            connection = sqlite3.connect(candidate)
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            has_questions_table = cursor.fetchone() is not None
            if has_questions_table:
                cursor.execute("SELECT COUNT(*) FROM questions")
                row_count = cursor.fetchone()[0]
                connection.close()
                if row_count > 0:
                    return candidate
            connection.close()
        except Exception:
            continue

    return candidates[0]


DB_PATH = _resolve_db_path()

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    if os.path.exists(DB_PATH):
        try:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='addphoto'")
            if cursor.fetchone() is not None:
                cursor.execute("PRAGMA table_info(addphoto)")
                columns = {row[1] for row in cursor.fetchall()}
                if 'user_question_header' not in columns:
                    connection.close()
                    engine.dispose()
                    if os.path.exists(DB_PATH):
                        os.remove(DB_PATH)
                    Base.metadata.drop_all(bind=engine)
                    Base.metadata.create_all(bind=engine)
                    return
            connection.close()
        except Exception:
            if 'connection' in locals():
                connection.close()
    Base.metadata.create_all(bind=engine)







class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    voted_questions = Column(String, default="")  # Store voted question IDs as a comma-separated string
    vote=Column(String, default="")  # Store the user's vote as a string (e.g., "option1" or "option2")
    last_question_id = Column(Integer, nullable=True)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(String, index=True)
    option1 = Column(String)
    option2 = Column(String)

class User_questions(Base):
    __tablename__ = "user_questions"

    header = Column(String, primary_key=True, index=True)
    question_text = Column(String, index=True)
    option1 = Column(String)
    option2 = Column(String)
    username = Column(String, index=True)
    question_id = Column(Integer, index=True)
    photos = relationship(
        "addphoto",
        back_populates="user_question",
        cascade="all, delete-orphan",
    )


class addphoto(Base):
    __tablename__ = "addphoto"

    id = Column(Integer, primary_key=True, index=True)
    user_question_header = Column(String, ForeignKey("user_questions.header"), nullable=False)
    imageurl = Column(String, nullable=False)

    user_question = relationship("User_questions", back_populates="photos")


class media (Base):
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    header = Column(String, index=True)
    question_text = Column(String, index=True)
    option1 = Column(String)
    option2 = Column(String)
    imageurl = Column(String)
    votes_option1 = Column(Integer, default=0)
    votes_option2 = Column(Integer, default=0)
    total_votes = Column(Integer, default=0)