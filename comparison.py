import json
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from database.database import get_db_connection
from ai.prompt_engine import PromptEngine
from ai.comparison import AIComparator

comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')

def get_current_user_id():
    return session.get('user_id', 1)

@comparison_bp.route('/', methods=['GET', 'POST'])
def index():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Load student context
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

    # Fetch last saved comparison
    cursor.execute("SELECT * FROM ai_comparisons WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    latest_db_comp = cursor.fetchone()
    conn.close()

    context = PromptEngine.format_student_context(profile, subjects, topics, exams)
    default_prompt = PromptEngine.get_improved_prompt(context)

    comparison_result = None

    if request.method == 'POST':
        prompt_text = request.form.get('prompt_text', '').strip() or default_prompt
        comparator = AIComparator(user_id)
        comparison_result = comparator.run_comparison(prompt_text, context)
        flash(f"AI Model comparison executed successfully! Best Model: {comparison_result['winner']}", "success")
    elif latest_db_comp:
        try:
            comparison_result = {
                'prompt_used': latest_db_comp['prompt_used'],
                'winner': latest_db_comp['selected_winner'],
                'winner_rationale': latest_db_comp['rationale'],
                'models': {
                    'chatgpt': json.loads(latest_db_comp['chatgpt_data']),
                    'gemini': json.loads(latest_db_comp['gemini_data']),
                    'claude': json.loads(latest_db_comp['claude_data'])
                },
                'comparison_table': [
                    json.loads(latest_db_comp['chatgpt_data'])['metrics'],
                    json.loads(latest_db_comp['gemini_data'])['metrics'],
                    json.loads(latest_db_comp['claude_data'])['metrics']
                ]
            }
        except Exception:
            comparator = AIComparator(user_id)
            comparison_result = comparator.run_comparison(default_prompt, context)
    else:
        # Generate initial default comparison so page immediately displays data
        comparator = AIComparator(user_id)
        comparison_result = comparator.run_comparison(default_prompt, context)

    return render_template(
        'comparison.html',
        comparison=comparison_result,
        default_prompt=default_prompt
    )
