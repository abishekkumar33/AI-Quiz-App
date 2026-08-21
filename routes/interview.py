"""
Interview routes: setup mock interview, generate questions, submit answer for
AI evaluation, view final report, download PDF.
"""
from flask import (Blueprint, render_template, request, redirect, url_for,
                    jsonify, send_file, abort)
from flask_login import login_required, current_user

from models import db, Interview, InterviewAnswer
from services.gemini_service import (
    GeminiServiceError, generate_interview_questions, evaluate_interview_answer,
)
from services.export_service import generate_interview_pdf

interview_bp = Blueprint('interview', __name__)


@interview_bp.route('/interview/new')
@login_required
def new_interview():
    return render_template('interview.html', mode='setup')


@interview_bp.route('/interview/generate', methods=['POST'])
@login_required
def generate():
    job_role = request.form.get('job_role', '').strip()
    experience_level = request.form.get('experience_level', 'Fresher')
    try:
        num_questions = int(request.form.get('num_questions', 5))
    except ValueError:
        num_questions = 5

    if not job_role:
        return jsonify({'success': False, 'message': 'Job role is required.'}), 400
    if experience_level not in ('Fresher', 'Intermediate', 'Experienced'):
        experience_level = 'Fresher'
    num_questions = max(3, min(15, num_questions))

    try:
        questions = generate_interview_questions(job_role, experience_level, num_questions)
        if not questions:
            return jsonify({'success': False, 'message': 'Could not generate questions. Try again.'}), 500

        interview = Interview(user_id=current_user.id, job_role=job_role,
                               experience_level=experience_level, num_questions=len(questions))
        db.session.add(interview)
        db.session.flush()

        for idx, q_text in enumerate(questions):
            answer = InterviewAnswer(interview_id=interview.id, question_text=q_text, order_index=idx)
            db.session.add(answer)

        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('interview.take_interview', interview_id=interview.id)})

    except GeminiServiceError as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 502
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error generating interview: {str(e)}'}), 500


@interview_bp.route('/interview/<int:interview_id>/take')
@login_required
def take_interview(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        abort(403)
    answers = InterviewAnswer.query.filter_by(interview_id=interview.id).order_by(InterviewAnswer.order_index).all()
    return render_template('interview.html', mode='take', interview=interview, answers=answers)


@interview_bp.route('/interview/answer/<int:answer_id>/evaluate', methods=['POST'])
@login_required
def evaluate_answer(answer_id):
    """AJAX: evaluate a single answer using Gemini and store the feedback."""
    answer = InterviewAnswer.query.get_or_404(answer_id)
    interview = Interview.query.get_or_404(answer.interview_id)
    if interview.user_id != current_user.id:
        abort(403)

    payload = request.get_json(silent=True) or {}
    user_answer = payload.get('answer', '').strip()

    try:
        evaluation = evaluate_interview_answer(
            interview.job_role, interview.experience_level, answer.question_text, user_answer
        )
        answer.user_answer = user_answer
        answer.score = evaluation['score']
        answer.strengths = evaluation['strengths']
        answer.weaknesses = evaluation['weaknesses']
        answer.improved_answer = evaluation['improved_answer']
        answer.tips = evaluation['tips']
        db.session.commit()

        return jsonify({'success': True, 'evaluation': evaluation})
    except GeminiServiceError as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 502
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error evaluating answer: {str(e)}'}), 500


@interview_bp.route('/interview/<int:interview_id>/complete', methods=['POST'])
@login_required
def complete_interview(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        abort(403)

    answers = InterviewAnswer.query.filter_by(interview_id=interview.id).all()
    scored = [a.score for a in answers if a.score is not None]
    interview.average_score = round(sum(scored) / len(scored), 1) if scored else 0.0
    interview.completed = True
    db.session.commit()

    return jsonify({'success': True, 'redirect': url_for('interview.interview_result', interview_id=interview.id)})


@interview_bp.route('/interview/<int:interview_id>/result')
@login_required
def interview_result(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        abort(403)
    answers = InterviewAnswer.query.filter_by(interview_id=interview.id).order_by(InterviewAnswer.order_index).all()
    return render_template('interview_result.html', interview=interview, answers=answers)


@interview_bp.route('/interview/<int:interview_id>/pdf')
@login_required
def download_interview_pdf(interview_id):
    interview = Interview.query.get_or_404(interview_id)
    if interview.user_id != current_user.id:
        abort(403)
    answers = InterviewAnswer.query.filter_by(interview_id=interview.id).order_by(InterviewAnswer.order_index).all()

    buffer = generate_interview_pdf(interview, answers)
    filename = f"interview_report_{interview.job_role.replace(' ', '_')}_{interview.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
