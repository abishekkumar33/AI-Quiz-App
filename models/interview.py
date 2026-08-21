"""
Interview models: Interview (a mock interview session), InterviewAnswer
(each question, user's answer, and AI evaluation).
"""
from datetime import datetime
from models import db


class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_role = db.Column(db.String(150), nullable=False)
    experience_level = db.Column(db.String(30), nullable=False)  # Fresher, Intermediate, Experienced
    num_questions = db.Column(db.Integer, nullable=False)
    average_score = db.Column(db.Float, default=0.0)  # out of 10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

    answers = db.relationship('InterviewAnswer', backref='interview', lazy=True, cascade='all, delete-orphan')


class InterviewAnswer(db.Model):
    __tablename__ = 'interview_answers'

    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey('interviews.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Text)
    score = db.Column(db.Float, default=0.0)          # out of 10
    strengths = db.Column(db.Text)
    weaknesses = db.Column(db.Text)
    improved_answer = db.Column(db.Text)
    tips = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
