"""
Quiz routes: generate quiz (via Gemini), take quiz, submit & score, view result,
download quiz PDF.
"""
import time
from flask import (Blueprint, render_template, request, redirect, url_for,
                    flash, jsonify, send_file, abort)
from flask_login import login_required, current_user

from models import db, Quiz, QuizQuestion, QuizResult
from services.gemini_service import GeminiServiceError, generate_quiz_questions
from services.export_service import generate_quiz_pdf

quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/quiz/new', methods=['GET'])
@login_required
def new_quiz():
    """Form to configure a new quiz."""
    return render_template('quiz.html', mode='setup')


@quiz_bp.route('/quiz/generate', methods=['POST'])
@login_required
def generate():
    """AJAX endpoint: generate quiz questions with Gemini and persist them."""
    topic = request.form.get('topic', '').strip()
    difficulty = request.form.get('difficulty', 'Medium')
    try:
        num_questions = int(request.form.get('num_questions', 5))
    except ValueError:
        num_questions = 5

    if not topic:
        return jsonify({'success': False, 'message': 'Topic is required.'}), 400
    if difficulty not in ('Easy', 'Medium', 'Hard'):
        difficulty = 'Medium'
    if num_questions not in (5, 10, 15, 20):
        num_questions = 5

    try:
        questions_data = generate_quiz_questions(topic, difficulty, num_questions)
        if not questions_data:
            return jsonify({'success': False, 'message': 'Could not generate questions. Try again.'}), 500

        quiz = Quiz(user_id=current_user.id, topic=topic, difficulty=difficulty,
                    num_questions=len(questions_data))
        db.session.add(quiz)
        db.session.flush()  # get quiz.id

        for idx, q in enumerate(questions_data):
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q['question'],
                option_a=q['option_a'], option_b=q['option_b'],
                option_c=q['option_c'], option_d=q['option_d'],
                correct_option=q['correct_option'],
                explanation=q.get('explanation', ''),
                order_index=idx,
            )
            db.session.add(question)

        db.session.commit()
        return jsonify({'success': True, 'quiz_id': quiz.id, 'redirect': url_for('quiz.take_quiz', quiz_id=quiz.id)})

    except GeminiServiceError as exc:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(exc)}), 502
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error generating quiz: {str(e)}'}), 500


@quiz_bp.route('/quiz/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        abort(403)
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order_index).all()
    return render_template('quiz.html', mode='take', quiz=quiz, questions=questions)


@quiz_bp.route('/quiz/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.user_id != current_user.id:
        abort(403)

    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order_index).all()
    payload = request.get_json(silent=True) or {}
    answers = payload.get('answers', {})  # {question_id(str): selected_option}
    time_taken = int(payload.get('time_taken_seconds', 0))

    score = 0
    answer_records = []
    for q in questions:
        selected = answers.get(str(q.id))
        is_correct = (selected == q.correct_option)
        if is_correct:
            score += 1
        answer_records.append({
            'question_id': q.id,
            'selected_option': selected,
            'is_correct': is_correct,
        })

    total = len(questions)
    percentage = round((score / total) * 100, 1) if total else 0.0

    result = QuizResult(
        quiz_id=quiz.id, user_id=current_user.id,
        score=score, total_questions=total, percentage=percentage,
        time_taken_seconds=time_taken,
    )
    result.set_answers(answer_records)
    db.session.add(result)
    db.session.commit()

    return jsonify({'success': True, 'redirect': url_for('quiz.quiz_result', result_id=result.id)})


@quiz_bp.route('/quiz/result/<int:result_id>')
@login_required
def quiz_result(result_id):
    result = QuizResult.query.get_or_404(result_id)
    if result.user_id != current_user.id:
        abort(403)
    quiz = Quiz.query.get_or_404(result.quiz_id)
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order_index).all()
    answers_by_qid = {a['question_id']: a for a in result.get_answers()}

    return render_template('quiz_result.html', quiz=quiz, result=result,
                            questions=questions, answers_by_qid=answers_by_qid)


@quiz_bp.route('/quiz/result/<int:result_id>/pdf')
@login_required
def download_quiz_pdf(result_id):
    result = QuizResult.query.get_or_404(result_id)
    if result.user_id != current_user.id:
        abort(403)
    quiz = Quiz.query.get_or_404(result.quiz_id)
    questions = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.order_index).all()
    answers_by_qid = {a['question_id']: a for a in result.get_answers()}

    buffer = generate_quiz_pdf(quiz, result, questions, answers_by_qid)
    filename = f"quiz_report_{quiz.topic.replace(' ', '_')}_{result.id}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
