"""
History routes - browse past quizzes & interviews, search, CSV export.
"""
import io
from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user

from models import db, Quiz, QuizResult, Interview
from services.export_service import generate_quiz_history_csv, generate_interview_history_csv

history_bp = Blueprint('history', __name__)


@history_bp.route('/history')
@login_required
def index():
    tab = request.args.get('tab', 'quizzes')
    search = request.args.get('q', '').strip()

    quiz_query = (db.session.query(QuizResult, Quiz)
                  .join(Quiz, QuizResult.quiz_id == Quiz.id)
                  .filter(QuizResult.user_id == current_user.id))
    if search:
        quiz_query = quiz_query.filter(Quiz.topic.ilike(f'%{search}%'))
    quiz_results = quiz_query.order_by(QuizResult.submitted_at.desc()).all()

    interview_query = Interview.query.filter_by(user_id=current_user.id, completed=True)
    if search:
        interview_query = interview_query.filter(Interview.job_role.ilike(f'%{search}%'))
    interviews = interview_query.order_by(Interview.created_at.desc()).all()

    return render_template('history.html', tab=tab, search=search,
                            quiz_results=quiz_results, interviews=interviews)


@history_bp.route('/history/quizzes/export/csv')
@login_required
def export_quiz_csv():
    results = (db.session.query(QuizResult, Quiz)
               .join(Quiz, QuizResult.quiz_id == Quiz.id)
               .filter(QuizResult.user_id == current_user.id)
               .order_by(QuizResult.submitted_at.desc()).all())
    buffer = generate_quiz_history_csv(results)
    bytes_buffer = io.BytesIO(buffer.getvalue().encode('utf-8'))
    return send_file(
        bytes_buffer,
        as_attachment=True, download_name='quiz_history.csv', mimetype='text/csv'
    )


@history_bp.route('/history/interviews/export/csv')
@login_required
def export_interview_csv():
    interviews = (Interview.query.filter_by(user_id=current_user.id, completed=True)
                  .order_by(Interview.created_at.desc()).all())
    buffer = generate_interview_history_csv(interviews)
    bytes_buffer = io.BytesIO(buffer.getvalue().encode('utf-8'))
    return send_file(
        bytes_buffer,
        as_attachment=True, download_name='interview_history.csv', mimetype='text/csv'
    )
