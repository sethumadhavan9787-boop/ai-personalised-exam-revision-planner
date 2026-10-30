from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import get_db_connection

subjects_bp = Blueprint('subjects', __name__, url_prefix='/subjects')

def get_current_user_id():
    return session.get('user_id', 1)

@subjects_bp.route('/')
def list_subjects():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY difficulty_level DESC", (user_id,))
    subjects = [dict(s) for s in cursor.fetchall()]

    # Fetch topics for each subject
    for s in subjects:
        cursor.execute("SELECT * FROM topics WHERE subject_id = ? AND user_id = ? ORDER BY is_weak DESC, name ASC", (s['id'], user_id))
        s['topics'] = [dict(t) for t in cursor.fetchall()]
        s['weak_count'] = sum(1 for t in s['topics'] if t.get('is_weak'))
        s['strong_count'] = sum(1 for t in s['topics'] if t.get('is_strong'))

    conn.close()
    return render_template('subjects.html', subjects=subjects)

@subjects_bp.route('/add', methods=['POST'])
def add_subject():
    user_id = get_current_user_id()
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    difficulty = int(request.form.get('difficulty_level', 3))
    color_tag = request.form.get('color_tag', '#4f46e5')

    if not name:
        flash("Subject name is required.", "warning")
        return redirect(url_for('subjects.list_subjects'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subjects (user_id, name, code, difficulty_level, color_tag)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, name, code, difficulty, color_tag))
    conn.commit()
    conn.close()

    flash(f"Subject '{name}' added successfully.", "success")
    return redirect(url_for('subjects.list_subjects'))

@subjects_bp.route('/delete/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
    conn.commit()
    conn.close()

    flash("Subject and associated topics deleted.", "info")
    return redirect(url_for('subjects.list_subjects'))

@subjects_bp.route('/topics/add', methods=['POST'])
def add_topic():
    user_id = get_current_user_id()
    subject_id = int(request.form.get('subject_id'))
    name = request.form.get('name', '').strip()
    is_weak = 1 if request.form.get('is_weak') else 0
    is_strong = 1 if request.form.get('is_strong') else 0
    estimated_hours = float(request.form.get('estimated_hours', 2.0))
    mastery_level = int(request.form.get('mastery_level', 2))
    notes = request.form.get('notes', '').strip()

    if not name:
        flash("Topic name is required.", "warning")
        return redirect(url_for('subjects.list_subjects'))

    # If marked weak, cannot be strong simultaneously
    if is_weak:
        is_strong = 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO topics (subject_id, user_id, name, is_weak, is_strong, estimated_hours, mastery_level, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (subject_id, user_id, name, is_weak, is_strong, estimated_hours, mastery_level, notes))
    conn.commit()
    conn.close()

    flash(f"Topic '{name}' added.", "success")
    return redirect(url_for('subjects.list_subjects'))

@subjects_bp.route('/topics/toggle-weak/<int:topic_id>', methods=['POST'])
def toggle_weak(topic_id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_weak FROM topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
    row = cursor.fetchone()
    if row:
        new_weak = 0 if row['is_weak'] else 1
        new_strong = 0 if new_weak == 1 else 0
        cursor.execute("UPDATE topics SET is_weak = ?, is_strong = ? WHERE id = ? AND user_id = ?",
                       (new_weak, new_strong, topic_id, user_id))
        conn.commit()
    conn.close()
    return redirect(url_for('subjects.list_subjects'))

@subjects_bp.route('/topics/delete/<int:topic_id>', methods=['POST'])
def delete_topic(topic_id):
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM topics WHERE id = ? AND user_id = ?", (topic_id, user_id))
    conn.commit()
    conn.close()
    flash("Topic deleted.", "info")
    return redirect(url_for('subjects.list_subjects'))
