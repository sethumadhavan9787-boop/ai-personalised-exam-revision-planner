from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import get_db_connection

prompts_bp = Blueprint('prompts', __name__, url_prefix='/prompts')

def get_current_user_id():
    return session.get('user_id', 1)

@prompts_bp.route('/')
def index():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    category_filter = request.args.get('category', 'all')

    query = "SELECT * FROM saved_prompts WHERE (user_id = ? OR is_system_default = 1)"
    params = [user_id]

    if category_filter != 'all':
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    prompts = [dict(p) for p in cursor.fetchall()]

    # Categories list for filter
    cursor.execute("SELECT DISTINCT category FROM saved_prompts ORDER BY category ASC")
    categories = [r['category'] for r in cursor.fetchall()]

    conn.close()

    return render_template(
        'prompts.html',
        prompts=prompts,
        categories=categories,
        selected_category=category_filter
    )

@prompts_bp.route('/add', methods=['POST'])
def add_prompt():
    user_id = get_current_user_id()
    title = request.form.get('title', '').strip()
    category = request.form.get('category', 'General Study').strip()
    baseline = request.form.get('baseline_prompt', '').strip()
    improved = request.form.get('improved_prompt', '').strip()
    explanation = request.form.get('explanation', '').strip()

    if not title or not improved:
        flash("Title and improved prompt are required.", "warning")
        return redirect(url_for('prompts.index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO saved_prompts (user_id, title, category, baseline_prompt, improved_prompt, explanation, is_system_default)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    ''', (user_id, title, category, baseline, improved, explanation))
    conn.commit()
    conn.close()

    flash("Custom prompt added to your library!", "success")
    return redirect(url_for('prompts.index'))
