from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database.database import get_db_connection

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable')

def get_current_user_id():
    return session.get('user_id', 1)

@timetable_bp.route('/')
def view_timetable():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get active plan or latest plan
    cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? AND is_active = 1", (user_id,))
    active_plan = cursor.fetchone()
    if not active_plan:
        cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        active_plan = cursor.fetchone()

    cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? ORDER BY id ASC", (user_id,))
    all_plans = [dict(p) for p in cursor.fetchall()]

    if not active_plan:
        conn.close()
        flash("No revision plan generated yet. Please click 'Generate Plans' to begin.", "info")
        return redirect(url_for('planner.index'))

    # Filters
    selected_week = request.args.get('week', '1') # Default to Week 1
    selected_subject = request.args.get('subject', 'all')
    selected_priority = request.args.get('priority', 'all')

    query = """
        SELECT s.*, sub.name as subject_name, sub.code as subject_code, sub.color_tag,
               t.name as topic_name, t.is_weak as topic_is_weak
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE s.plan_id = ? AND s.user_id = ?
    """
    params = [active_plan['id'], user_id]

    if selected_week != 'all':
        query += " AND s.week_number = ?"
        params.append(int(selected_week))

    if selected_subject != 'all':
        query += " AND s.subject_id = ?"
        params.append(int(selected_subject))

    if selected_priority != 'all':
        query += " AND s.priority = ?"
        params.append(selected_priority)

    query += " ORDER BY s.session_date ASC, s.start_time ASC"

    cursor.execute(query, params)
    sessions = [dict(s) for s in cursor.fetchall()]

    # Fetch subjects for filter dropdown
    cursor.execute("SELECT * FROM subjects WHERE user_id = ?", (user_id,))
    subjects = [dict(s) for s in cursor.fetchall()]

    # Organize sessions by day for weekly calendar layout
    calendar_days = {}
    for s in sessions:
        d = s['session_date']
        calendar_days.setdefault(d, {
            'date': d,
            'day_name': s['day_of_week'],
            'sessions': []
        })['sessions'].append(s)

    conn.close()

    return render_template(
        'timetable.html',
        active_plan=active_plan,
        all_plans=all_plans,
        sessions=sessions,
        calendar_days=list(calendar_days.values()),
        subjects=subjects,
        selected_week=selected_week,
        selected_subject=selected_subject,
        selected_priority=selected_priority
    )

@timetable_bp.route('/update-status', methods=['POST'])
def update_status():
    user_id = get_current_user_id()
    session_id = request.form.get('session_id')
    new_status = request.form.get('status')

    if new_status not in ['Pending', 'Completed', 'Skipped']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    completed_at = datetime.now().isoformat() if new_status == 'Completed' else None

    cursor.execute('''
        UPDATE study_sessions
        SET status = ?, completed_at = ?
        WHERE id = ? AND user_id = ?
    ''', (new_status, completed_at, session_id, user_id))
    conn.commit()
    conn.close()

    # If request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'status': new_status})

    return redirect(request.referrer or url_for('timetable.view_timetable'))
