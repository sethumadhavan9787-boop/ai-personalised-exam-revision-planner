from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import get_db_connection
from ai.planner import AIRevisionPlanner
from ai.prompt_engine import PromptEngine
from validation.timetable_validator import TimetableValidator

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

def get_current_user_id():
    return session.get('user_id', 1)

@planner_bp.route('/')
def index():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Load existing plans for this user
    cursor.execute("SELECT * FROM revision_plans WHERE user_id = ? ORDER BY id ASC", (user_id,))
    plans = [dict(p) for p in cursor.fetchall()]

    # Student context for prompt preview
    cursor.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()

    cursor.execute("SELECT * FROM subjects WHERE user_id = ?", (user_id,))
    subjects = [dict(s) for s in cursor.fetchall()]

    cursor.execute("SELECT * FROM topics WHERE user_id = ?", (user_id,))
    topics = [dict(t) for t in cursor.fetchall()]

    cursor.execute("""
        SELECT e.*, s.name as subject_name
        FROM examinations e
        JOIN subjects s ON e.subject_id = s.id
        WHERE e.user_id = ?
        ORDER BY e.exam_date ASC
    """, (user_id,))
    exams = [dict(e) for e in cursor.fetchall()]

    conn.close()

    context = PromptEngine.format_student_context(profile, subjects, topics, exams)
    baseline_prompt = PromptEngine.get_baseline_prompt(context)
    improved_prompt = PromptEngine.get_improved_prompt(context)

    # If plans exist, get validation report for the active one
    active_plan = next((p for p in plans if p.get('is_active')), plans[0] if plans else None)
    validation_report = None
    if active_plan:
        validator = TimetableValidator(active_plan['id'], user_id)
        validation_report = validator.validate()
        validator.close()

    return render_template(
        'planner.html',
        plans=plans,
        active_plan=active_plan,
        profile=profile,
        subjects=subjects,
        topics=topics,
        exams=exams,
        baseline_prompt=baseline_prompt,
        improved_prompt=improved_prompt,
        validation_report=validation_report,
        today_date=date.today().isoformat()
    )

@planner_bp.route('/generate', methods=['POST'])
def generate_plans():
    user_id = get_current_user_id()
    start_date = request.form.get('start_date', date.today().isoformat())

    planner = AIRevisionPlanner(user_id)
    new_plans = planner.generate_all_plans(start_date=start_date)

    if not new_plans or not new_plans[0]:
        flash("Could not generate revision plans. Please make sure you have added at least one subject first.", "warning")
        return redirect(url_for('subjects.list_subjects'))

    flash("Successfully generated all 3 AI Revision Plans (Balanced, Weak Topic Priority, and Exam Deadline Priority) with automated validation!", "success")
    return redirect(url_for('planner.index'))

@planner_bp.route('/set-active/<int:plan_id>', methods=['POST'])
def set_active(plan_id):
    user_id = get_current_user_id()
    planner = AIRevisionPlanner(user_id)
    planner.set_active_plan(plan_id)
    flash("Active revision plan updated. Your dashboard and exports now reflect this plan.", "success")
    return redirect(url_for('planner.index'))

@planner_bp.route('/validate/<int:plan_id>')
def validate_plan(plan_id):
    user_id = get_current_user_id()
    validator = TimetableValidator(plan_id, user_id)
    report = validator.validate()
    validator.close()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM revision_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
    plan = cursor.fetchone()
    conn.close()

    return render_template('planner.html', plan_to_validate=plan, specific_validation=report, validation_modal=True)
