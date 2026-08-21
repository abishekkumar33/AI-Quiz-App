"""
Student dashboard route.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import Quiz, QuizResult, Interview

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    interview_count = Interview.query.filter_by(user_id=current_user.id, completed=True).count()

    recent_results = (QuizResult.query
                       .filter_by(user_id=current_user.id)
                       .order_by(QuizResult.submitted_at.desc())
                       .limit(3).all())
    recent_interviews = (Interview.query
                          .filter_by(user_id=current_user.id, completed=True)
                          .order_by(Interview.created_at.desc())
                          .limit(3).all())

    return render_template(
        'dashboard.html',
        quiz_count=quiz_count,
        interview_count=interview_count,
        recent_results=recent_results,
        recent_interviews=recent_interviews,
    )
