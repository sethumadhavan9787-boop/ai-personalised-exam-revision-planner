from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import get_db_connection

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

def get_current_user_id():
    return session.get('user_id', 1)

@exams_bp.route('/')
def list_exams():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.*, s.name as subject_name, s.code as subject_code, s.color_tag, s.difficulty_level
        FROM examinations e
        JOIN subjects s ON e.subject_id = s.id
        WHERE e.user_id = ?
        ORDER BY e.exam_date ASC
    """, (user_id,))
    exams = [dict(e) for e in cursor.fetchall()]

    today = date.today()
    for e in exams:
        ed = datetime.strptime(e['exam_date'], "%Y-%m-%d").date()
        days_left = (ed - today).days
        e['days_left'] = days_left
        e['status_badge'] = 'Past' if days_left < 0 else ('Today' if days_left == 0 else f"{days_left} Days Remaining")
        e['is_urgent'] = 0 <= days_left <= 7

    cursor.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY name ASC", (user_id,))
    subjects = cursor.fetchall()

    conn.close()
    return render_template('exams.html', exams=exams, subjects=subjects, today_date=today.isoformat())

@exams_bp.route('/add', methods=['POST'])
def add_exam():
    user_id = get_current_user_id()
    subject_id = int(request.form.get('subject_id'))
    exam_date = request.form.get('exam_date')
    exam_time = request.form.get('exam_time', '09:30 AM')
    venue = request.form.get('venue', 'Main Exam Hall').strip()
    weightage = int(request.form.get('weightage_percentage', 50))
    target_grade = request.form.get('target_grade', 'A').strip()
    notes = request.form.get('notes', '').strip()

    if not exam_date:
        flash("Examination date is required.", "warning")
        return redirect(url_for('exams.list_exams'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO examinations (user_id, subject_id, exam_date, exam_time, venue, weightage_percentage, target_grade, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, subject_id, exam_date, exam_time, venue, weightage, target_grade, notes))
    conn.commit()
    conn.close()

    flash("Examination date added successfully. The AI planner will prioritize revision leading up to this date.", "success")
    return redirect(url_for('exams.list_exams'))

@exams_bp.route('/delete/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM examinations WHERE id = ? AND user_id = ?", (exam_id, user_id))
    conn.commit()
    conn.close()
    flash("Examination removed.", "info")
    return redirect(url_for('exams.list_exams'))
