"""
Quiz models: Quiz (a generated quiz session), QuizQuestion (individual MCQs),
QuizResult (a user's completed attempt + score summary).
"""
import json
from datetime import datetime
from models import db


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # Easy, Medium, Hard
    num_questions = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')
    results = db.relationship('QuizResult', backref='quiz', lazy=True, cascade='all, delete-orphan')


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_option = db.Column(db.String(1), nullable=False)  # 'A' | 'B' | 'C' | 'D'
    explanation = db.Column(db.Text)
    order_index = db.Column(db.Integer, default=0)

    def options_dict(self):
        return {'A': self.option_a, 'B': self.option_b, 'C': self.option_c, 'D': self.option_d}


class QuizResult(db.Model):
    __tablename__ = 'quiz_results'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)          # correct answers
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    time_taken_seconds = db.Column(db.Integer, default=0)
    answers_json = db.Column(db.Text)  # JSON list of {question_id, selected_option, is_correct}
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_answers(self):
        try:
            return json.loads(self.answers_json) if self.answers_json else []
        except (TypeError, ValueError):
            return []

    def set_answers(self, answers_list):
        self.answers_json = json.dumps(answers_list)
