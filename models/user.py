"""
User model - handles authentication and profile data.
"""
from datetime import datetime
from flask_login import UserMixin
from models import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.String(255), nullable=True, default='')
    avatar = db.Column(db.String(255), nullable=True, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade='all, delete-orphan')
    interviews = db.relationship('Interview', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'bio': self.bio,
            'created_at': self.created_at.strftime('%B %d, %Y') if self.created_at else '',
        }
