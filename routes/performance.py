"""
Performance analysis routes - aggregate statistics & chart data.
"""
from collections import defaultdict
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from models import db, Quiz, QuizResult, Interview

performance_bp = Blueprint('performance', __name__)


def _compute_stats(user_id):
    results = (db.session.query(QuizResult, Quiz)
               .join(Quiz, QuizResult.quiz_id == Quiz.id)
               .filter(QuizResult.user_id == user_id)
               .order_by(QuizResult.submitted_at.asc())
               .all())

    total_quizzes = len(results)
    scores = [r.percentage for r, q in results]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    highest = round(max(scores), 1) if scores else 0.0
    lowest = round(min(scores), 1) if scores else 0.0

    topic_perf = defaultdict(list)
    difficulty_perf = defaultdict(list)
    for r, q in results:
        topic_perf[q.topic].append(r.percentage)
        difficulty_perf[q.difficulty].append(r.percentage)

    topic_wise = [{'topic': t, 'average': round(sum(v) / len(v), 1), 'count': len(v)}
                  for t, v in topic_perf.items()]
    difficulty_wise = [{'difficulty': d, 'average': round(sum(v) / len(v), 1), 'count': len(v)}
                        for d, v in difficulty_perf.items()]

    interviews = Interview.query.filter_by(user_id=user_id, completed=True).all()
    interview_avg = (round(sum(i.average_score for i in interviews) / len(interviews), 1)
                      if interviews else 0.0)

    # Score trend over time (last 10 quiz attempts)
    trend = [{'label': q.topic[:15], 'score': r.percentage,
              'date': r.submitted_at.strftime('%b %d')} for r, q in results[-10:]]

    return {
        'total_quizzes': total_quizzes,
        'avg_score': avg_score,
        'highest_score': highest,
        'lowest_score': lowest,
        'interview_count': len(interviews),
        'interview_avg': interview_avg,
        'topic_wise': topic_wise,
        'difficulty_wise': difficulty_wise,
        'trend': trend,
    }


@performance_bp.route('/performance')
@login_required
def index():
    stats = _compute_stats(current_user.id)

    recent_quiz = (db.session.query(QuizResult, Quiz)
                   .join(Quiz, QuizResult.quiz_id == Quiz.id)
                   .filter(QuizResult.user_id == current_user.id)
                   .order_by(QuizResult.submitted_at.desc()).limit(5).all())
    recent_interviews = (Interview.query.filter_by(user_id=current_user.id, completed=True)
                          .order_by(Interview.created_at.desc()).limit(5).all())

    return render_template('performance.html', stats=stats,
                            recent_quiz=recent_quiz, recent_interviews=recent_interviews)


@performance_bp.route('/api/performance/stats')
@login_required
def stats_json():
    """AJAX endpoint used by Chart.js on the performance page."""
    return jsonify(_compute_stats(current_user.id))
