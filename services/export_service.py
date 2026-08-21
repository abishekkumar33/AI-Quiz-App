"""
Export service - generates downloadable PDF reports and CSV files for
quiz results and interview attempts.
"""
import io
import csv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TitleCustom', fontSize=20, spaceAfter=12,
                               textColor=colors.HexColor('#4f46e5'), leading=24))
    styles.add(ParagraphStyle(name='Meta', fontSize=10, textColor=colors.grey, spaceAfter=16))
    styles.add(ParagraphStyle(name='QHeading', fontSize=12, spaceBefore=14, spaceAfter=4,
                               textColor=colors.HexColor('#111827')))
    styles.add(ParagraphStyle(name='Body', fontSize=10, leading=14))
    styles.add(ParagraphStyle(name='Correct', fontSize=10, textColor=colors.HexColor('#16a34a')))
    styles.add(ParagraphStyle(name='Incorrect', fontSize=10, textColor=colors.HexColor('#dc2626')))
    return styles


def generate_quiz_pdf(quiz, result, questions, answers_by_qid):
    """Build a PDF report for one quiz attempt. Returns BytesIO buffer."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = _base_styles()
    story = []

    story.append(Paragraph("AI Quiz & Mock Interview - Quiz Report", styles['TitleCustom']))
    story.append(Paragraph(
        f"Topic: {quiz.topic} &nbsp;|&nbsp; Difficulty: {quiz.difficulty} &nbsp;|&nbsp; "
        f"Date: {result.submitted_at.strftime('%B %d, %Y %H:%M')}", styles['Meta']))

    summary_data = [
        ['Score', f"{result.score} / {result.total_questions}"],
        ['Percentage', f"{result.percentage:.1f}%"],
        ['Time Taken', f"{result.time_taken_seconds // 60}m {result.time_taken_seconds % 60}s"],
    ]
    t = Table(summary_data, colWidths=[6*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eef2ff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    for idx, q in enumerate(questions, start=1):
        ans = answers_by_qid.get(q.id, {})
        selected = ans.get('selected_option', 'Not answered')
        is_correct = ans.get('is_correct', False)

        story.append(Paragraph(f"Q{idx}. {q.question_text}", styles['QHeading']))
        opts = q.options_dict()
        for key in ['A', 'B', 'C', 'D']:
            prefix = "&#10003;" if key == q.correct_option else ("&#10007;" if key == selected else "-")
            story.append(Paragraph(f"{prefix} {key}. {opts[key]}", styles['Body']))

        result_style = styles['Correct'] if is_correct else styles['Incorrect']
        story.append(Paragraph(
            f"Your answer: {selected} | Correct answer: {q.correct_option} | "
            f"{'Correct' if is_correct else 'Incorrect'}", result_style))
        if q.explanation:
            story.append(Paragraph(f"Explanation: {q.explanation}", styles['Body']))
        story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_interview_pdf(interview, answers):
    """Build a PDF report for one interview attempt. Returns BytesIO buffer."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = _base_styles()
    story = []

    story.append(Paragraph("AI Quiz & Mock Interview - Interview Report", styles['TitleCustom']))
    story.append(Paragraph(
        f"Role: {interview.job_role} &nbsp;|&nbsp; Level: {interview.experience_level} &nbsp;|&nbsp; "
        f"Date: {interview.created_at.strftime('%B %d, %Y %H:%M')}", styles['Meta']))

    story.append(Paragraph(f"Overall Average Score: {interview.average_score:.1f} / 10", styles['QHeading']))
    story.append(Spacer(1, 10))

    for idx, a in enumerate(answers, start=1):
        story.append(Paragraph(f"Q{idx}. {a.question_text}", styles['QHeading']))
        story.append(Paragraph(f"<b>Your Answer:</b> {a.user_answer or '(No answer given)'}", styles['Body']))
        story.append(Paragraph(f"<b>Score:</b> {a.score:.1f} / 10", styles['Body']))
        if a.strengths:
            story.append(Paragraph(f"<b>Strengths:</b> {a.strengths}", styles['Correct']))
        if a.weaknesses:
            story.append(Paragraph(f"<b>Weaknesses:</b> {a.weaknesses}", styles['Incorrect']))
        if a.improved_answer:
            story.append(Paragraph(f"<b>Suggested Answer:</b> {a.improved_answer}", styles['Body']))
        if a.tips:
            story.append(Paragraph(f"<b>Tips:</b> {a.tips}", styles['Body']))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_quiz_history_csv(results):
    """results: list of (QuizResult, Quiz) tuples. Returns a string buffer (CSV text)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Date', 'Topic', 'Difficulty', 'Score', 'Total Questions', 'Percentage', 'Time Taken (s)'])
    for result, quiz in results:
        writer.writerow([
            result.submitted_at.strftime('%Y-%m-%d %H:%M'),
            quiz.topic, quiz.difficulty, result.score, result.total_questions,
            f"{result.percentage:.1f}", result.time_taken_seconds
        ])
    buffer.seek(0)
    return buffer


def generate_interview_history_csv(interviews):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Date', 'Job Role', 'Experience Level', 'Questions', 'Average Score'])
    for interview in interviews:
        writer.writerow([
            interview.created_at.strftime('%Y-%m-%d %H:%M'),
            interview.job_role, interview.experience_level,
            interview.num_questions, f"{interview.average_score:.1f}"
        ])
    buffer.seek(0)
    return buffer
