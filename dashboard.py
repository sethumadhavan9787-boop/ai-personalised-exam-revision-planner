from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, session, redirect, url_for
from database.database import get_db_connection
from validation.timetable_validator import TimetableValidator

dashboard_bp = Blueprint('dashboard', __name__)

def get_current_user_id():
    return session.get('user_id', 1)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    user_id = get_current_user_id()
    if not session.get('user_id'):
        return redirect(url_for('auth.demo_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Profile
    cursor.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()

    # 2. Subjects count & list
    cursor.execute("SELECT * FROM subjects WHERE user_id = ?", (user_id,))
    subjects = [dict(s) for s in cursor.fetchall()]
    total_subjects = len(subjects)

    # 3. Topics count & weak topics
    cursor.execute("SELECT * FROM topics WHERE user_id = ?", (user_id,))
    topics = [dict(t) for t in cursor.fetchall()]
    weak_topics = [t for t in topics if t.get('is_weak')]
    strong_topics = [t for t in topics if t.get('is_strong')]

    # 4. Upcoming examinations
    cursor.execute("""
        SELECT e.*, s.name as subject_name, s.code as subject_code, s.color_tag
        FROM examinations e
        JOIN subjects s ON e.subject_id = s.id
        WHERE e.user_id = ?
        ORDER BY e.exam_date ASC
    """, (user_id,))
    raw_exams = [dict(e) for e in cursor.fetchall()]
    today = date.today()

    upcoming_exams = []
    next_exam = None
    for e in raw_exams:
        e_date = datetime.strptime(e['exam_date'], "%Y-%m-%d").date()
        days_left = (e_date - today).days
        e['days_left'] = days_left
        e['is_urgent'] = 0 <= days_left <= 7
        upcoming_exams.append(e)
        if days_left >= 0 and next_exam is None:
            next_exam = e

    # 5. Active Revision Plan
    cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? AND is_active = 1", (user_id,))
    active_plan = cursor.fetchone()

    if not active_plan:
        cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        active_plan = cursor.fetchone()

    plan_sessions = []
    completed_sessions = 0
    pending_sessions = 0
    skipped_sessions = 0
    total_sessions = 0
    completion_rate = 0.0

    validation_result = None

    if active_plan:
        cursor.execute("""
            SELECT s.*, sub.name as subject_name, sub.code as subject_code, sub.color_tag,
                   t.name as topic_name, t.is_weak as topic_is_weak
            FROM study_sessions s
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE s.plan_id = ? AND s.user_id = ?
            ORDER BY s.session_date ASC, s.start_time ASC
        """, (active_plan['id'], user_id))
        plan_sessions = [dict(s) for s in cursor.fetchall()]

        total_sessions = len(plan_sessions)
        completed_sessions = sum(1 for s in plan_sessions if s['status'] == 'Completed')
        pending_sessions = sum(1 for s in plan_sessions if s['status'] == 'Pending')
        skipped_sessions = sum(1 for s in plan_sessions if s['status'] == 'Skipped')
        completion_rate = round((completed_sessions / total_sessions * 100), 1) if total_sessions else 0.0

        # Run quick validation for active plan
        validator = TimetableValidator(active_plan['id'], user_id)
        validation_result = validator.validate()
        validator.close()

    # Weekly distribution calculation for Chart.js
    week_distribution = {1: {'planned': 0, 'completed': 0}, 2: {'planned': 0, 'completed': 0},
                         3: {'planned': 0, 'completed': 0}, 4: {'planned': 0, 'completed': 0}}

    subject_hours_map = {}
    for s in plan_sessions:
        w = s.get('week_number', 1)
        dur_h = s['duration_minutes'] / 60.0
        if w in week_distribution:
            week_distribution[w]['planned'] += dur_h
            if s['status'] == 'Completed':
                week_distribution[w]['completed'] += dur_h

        subj_name = s['subject_name']
        subject_hours_map[subj_name] = subject_hours_map.get(subj_name, 0) + dur_h

    # Format chart data
    chart_weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
    chart_planned_hours = [round(week_distribution[w]['planned'], 1) for w in [1, 2, 3, 4]]
    chart_completed_hours = [round(week_distribution[w]['completed'], 1) for w in [1, 2, 3, 4]]

    chart_subject_labels = list(subject_hours_map.keys())
    chart_subject_data = [round(h, 1) for h in subject_hours_map.values()]

    # Today's sessions
    today_str = today.isoformat()
    todays_sessions = [s for s in plan_sessions if s['session_date'] == today_str]
    today_completed = sum(1 for s in todays_sessions if s['status'] == 'Completed')
    today_progress_rate = round((today_completed / len(todays_sessions) * 100), 1) if todays_sessions else 0

    # Weekly Free Hours
    weekly_free_hours = profile['weekly_free_hours'] if profile else 20.0
    total_plan_hours = active_plan['total_study_hours'] if active_plan else 0.0

    conn.close()

    return render_template(
        'dashboard.html',
        profile=profile,
        total_subjects=total_subjects,
        subjects=subjects,
        weak_topics=weak_topics,
        strong_topics=strong_topics,
        upcoming_exams=upcoming_exams,
        next_exam=next_exam,
        active_plan=active_plan,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        pending_sessions=pending_sessions,
        skipped_sessions=skipped_sessions,
        completion_rate=completion_rate,
        todays_sessions=todays_sessions,
        today_progress_rate=today_progress_rate,
        weekly_free_hours=weekly_free_hours,
        total_plan_hours=total_plan_hours,
        validation_result=validation_result,
        chart_weeks=chart_weeks,
        chart_planned_hours=chart_planned_hours,
        chart_completed_hours=chart_completed_hours,
        chart_subject_labels=chart_subject_labels,
        chart_subject_data=chart_subject_data
    )
