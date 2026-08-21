"""
Profile routes - view/update profile info, change password, view stats.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db, QuizResult, Interview
from utils.validators import is_valid_name, is_valid_password

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/profile')
@login_required
def index():
    quiz_count = QuizResult.query.filter_by(user_id=current_user.id).count()
    interview_count = Interview.query.filter_by(user_id=current_user.id, completed=True).count()
    avg_score = db.session.query(db.func.avg(QuizResult.percentage)).filter_by(
        user_id=current_user.id).scalar()
    avg_score = round(avg_score, 1) if avg_score else 0.0

    return render_template('profile.html', quiz_count=quiz_count,
                            interview_count=interview_count, avg_score=avg_score)


@profile_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    bio = request.form.get('bio', '').strip()

    if not is_valid_name(full_name):
        flash('Please enter a valid full name.', 'danger')
        return redirect(url_for('profile.index'))

    current_user.full_name = full_name
    current_user.bio = bio
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('profile.index'))


@profile_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile.index'))
    if not is_valid_password(new_password):
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('profile.index'))
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile.index'))

    current_user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully.', 'success')
    return redirect(url_for('profile.index'))
