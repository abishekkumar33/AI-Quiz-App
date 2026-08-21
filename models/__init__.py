"""
Models package.
Exposes the shared SQLAlchemy `db` instance and all ORM models.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

# Import models AFTER db is defined so they can use it.
from models.user import User
from models.quiz import Quiz, QuizQuestion, QuizResult
from models.interview import Interview, InterviewAnswer

__all__ = [
    "db", "bcrypt", "User",
    "Quiz", "QuizQuestion", "QuizResult",
    "Interview", "InterviewAnswer",
]
