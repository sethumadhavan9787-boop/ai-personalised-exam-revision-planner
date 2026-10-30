from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import get_db_connection

progress_bp = Blueprint('progress', __name__, url_prefix='/progress')

def get_current_user_id():
    return session.get('user_id', 1)

@progress_bp.route('/', methods=['GET', 'POST'])
def index():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Active plan
    cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? AND is_active = 1", (user_id,))
    active_plan = cursor.fetchone()
    if not active_plan:
        cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        active_plan = cursor.fetchone()

    # Handle reflection submission
    if request.method == 'POST' and request.form.get('action') == 'submit_reflection':
        week_num = int(request.form.get('week_number', 1))
        planned_h = float(request.form.get('planned_hours', 0.0))
        actual_h = float(request.form.get('actual_hours', 0.0))
        topics_done = int(request.form.get('topics_completed', 0))
        energy = int(request.form.get('energy_rating', 4))
        consistency = int(request.form.get('consistency_rating', 4))
        reflection_txt = request.form.get('reflection_text', '').strip()
        what_worked = request.form.get('what_worked', '').strip()
        what_improve = request.form.get('what_to_improve', '').strip()

        cursor.execute('''
            INSERT INTO weekly_reflections (
                user_id, week_number, planned_hours, actual_hours, topics_completed,
                energy_rating, consistency_rating, reflection_text, what_worked, what_to_improve
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, week_num, planned_h, actual_h, topics_done, energy, consistency, reflection_txt, what_worked, what_improve))
        conn.commit()
        flash(f"Weekly Reflection for Week {week_num} saved successfully!", "success")
        return redirect(url_for('progress.index'))

    # Weekly statistics breakdown
    weekly_stats = []
    total_planned = 0.0
    total_actual = 0.0
    total_completed_count = 0
    total_sessions_count = 0

    if active_plan:
        cursor.execute("""
            SELECT s.*, t.name as topic_name, sub.name as subject_name
            FROM study_sessions s
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE s.plan_id = ? AND s.user_id = ?
            ORDER BY s.week_number ASC, s.session_date ASC
        """, (active_plan['id'], user_id))
        sessions = [dict(s) for s in cursor.fetchall()]

        for w in [1, 2, 3, 4]:
            w_sessions = [s for s in sessions if s['week_number'] == w]
            w_planned_hours = sum(s['duration_minutes'] for s in w_sessions) / 60.0
            w_completed_sessions = [s for s in w_sessions if s['status'] == 'Completed']
            w_actual_hours = sum(s['duration_minutes'] for s in w_completed_sessions) / 60.0
            w_skipped_count = sum(1 for s in w_sessions if s['status'] == 'Skipped')
            w_pending_count = sum(1 for s in w_sessions if s['status'] == 'Pending')

            unique_topics_done = len(set(s['topic_id'] for s in w_completed_sessions if s['topic_id']))
            total_unique_topics = len(set(s['topic_id'] for s in w_sessions if s['topic_id']))

            completion_pct = round((len(w_completed_sessions) / len(w_sessions) * 100), 1) if w_sessions else 0.0

            weekly_stats.append({
                'week_number': w,
                'planned_hours': round(w_planned_hours, 1),
                'actual_hours': round(w_actual_hours, 1),
                'completed_sessions': len(w_completed_sessions),
                'total_sessions': len(w_sessions),
                'pending_sessions': w_pending_count,
                'skipped_sessions': w_skipped_count,
                'completed_topics': unique_topics_done,
                'remaining_topics': max(0, total_unique_topics - unique_topics_done),
                'completion_pct': completion_pct,
                'sessions': w_sessions
            })

            total_planned += w_planned_hours
            total_actual += w_actual_hours
            total_completed_count += len(w_completed_sessions)
            total_sessions_count += len(w_sessions)

    # Fetch reflections history
    cursor.execute("SELECT * FROM weekly_reflections WHERE user_id = ? ORDER BY week_number DESC, id DESC", (user_id,))
    reflections = [dict(r) for r in cursor.fetchall()]

    overall_pct = round((total_completed_count / total_sessions_count * 100), 1) if total_sessions_count else 0.0

    conn.close()

    return render_template(
        'progress.html',
        active_plan=active_plan,
        weekly_stats=weekly_stats,
        reflections=reflections,
        total_planned_hours=round(total_planned, 1),
        total_actual_hours=round(total_actual, 1),
        total_completed_count=total_completed_count,
        total_sessions_count=total_sessions_count,
        overall_completion_pct=overall_pct
    )
