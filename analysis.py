from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database.database import get_db_connection

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

def get_current_user_id():
    return session.get('user_id', 1)

@analysis_bp.route('/', methods=['GET', 'POST'])
def index():
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'save_data':
            b_hours = float(request.form.get('baseline_weekly_study_hours', 8.0))
            b_topics = int(request.form.get('baseline_topics_per_week', 3))
            b_weak_imp = float(request.form.get('baseline_weak_topic_improvement', 20.0))
            b_cons = float(request.form.get('baseline_consistency_rate', 45.0))
            b_quiz = float(request.form.get('baseline_mock_exam_score', 55.0))
            b_stress = int(request.form.get('baseline_stress_level', 8))

            p_hours = float(request.form.get('post_weekly_study_hours', 18.0))
            p_topics = int(request.form.get('post_topics_per_week', 8))
            p_weak_imp = float(request.form.get('post_weak_topic_improvement', 75.0))
            p_cons = float(request.form.get('post_consistency_rate', 85.0))
            p_quiz = float(request.form.get('post_mock_exam_score', 82.0))
            p_stress = int(request.form.get('post_stress_level', 4))
            feedback = request.form.get('student_feedback', '').strip()

            cursor.execute("SELECT id FROM before_after_analysis WHERE user_id = ?", (user_id,))
            exists = cursor.fetchone()

            if exists:
                cursor.execute('''
                    UPDATE before_after_analysis SET
                        baseline_weekly_study_hours = ?, baseline_topics_per_week = ?,
                        baseline_weak_topic_improvement = ?, baseline_consistency_rate = ?,
                        baseline_mock_exam_score = ?, baseline_stress_level = ?,
                        post_weekly_study_hours = ?, post_topics_per_week = ?,
                        post_weak_topic_improvement = ?, post_consistency_rate = ?,
                        post_mock_exam_score = ?, post_stress_level = ?, student_feedback = ?,
                        recorded_date = CURRENT_DATE
                    WHERE user_id = ?
                ''', (b_hours, b_topics, b_weak_imp, b_cons, b_quiz, b_stress,
                      p_hours, p_topics, p_weak_imp, p_cons, p_quiz, p_stress, feedback, user_id))
            else:
                cursor.execute('''
                    INSERT INTO before_after_analysis (
                        user_id, baseline_weekly_study_hours, baseline_topics_per_week,
                        baseline_weak_topic_improvement, baseline_consistency_rate,
                        baseline_mock_exam_score, baseline_stress_level,
                        post_weekly_study_hours, post_topics_per_week,
                        post_weak_topic_improvement, post_consistency_rate,
                        post_mock_exam_score, post_stress_level, student_feedback
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, b_hours, b_topics, b_weak_imp, b_cons, b_quiz, b_stress,
                      p_hours, p_topics, p_weak_imp, p_cons, p_quiz, p_stress, feedback))

            conn.commit()
            flash("Before & After analysis metrics updated successfully!", "success")
            return redirect(url_for('analysis.index'))

        elif action == 'load_demo_data':
            # Pre-load demo benchmark for evaluator
            cursor.execute("DELETE FROM before_after_analysis WHERE user_id = ?", (user_id,))
            cursor.execute('''
                INSERT INTO before_after_analysis (
                    user_id, baseline_weekly_study_hours, baseline_topics_per_week,
                    baseline_weak_topic_improvement, baseline_consistency_rate,
                    baseline_mock_exam_score, baseline_stress_level,
                    post_weekly_study_hours, post_topics_per_week,
                    post_weak_topic_improvement, post_consistency_rate,
                    post_mock_exam_score, post_stress_level, student_feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, 9.5, 3, 22.0, 48.0, 61.5, 8,
                21.0, 9, 79.5, 89.0, 86.0, 3,
                "Demo Evaluator Benchmark: The AI-generated timetable structure helped overcome initial inertia. Spacing out weak topics over 4 weeks prevented last-minute cramming and raised mock exam scores significantly."
            ))
            conn.commit()
            flash("Loaded Capstone Evaluator Sample Benchmark Data! Notice the metrics and radar comparison below.", "success")
            return redirect(url_for('analysis.index'))

    cursor.execute("SELECT * FROM before_after_analysis WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    analysis_record = cursor.fetchone()
    conn.close()

    if not analysis_record:
        # Default mock record
        analysis_record = {
            'baseline_weekly_study_hours': 9.0,
            'baseline_topics_per_week': 3,
            'baseline_weak_topic_improvement': 25.0,
            'baseline_consistency_rate': 45.0,
            'baseline_mock_exam_score': 60.0,
            'baseline_stress_level': 8,
            'post_weekly_study_hours': 20.0,
            'post_topics_per_week': 8,
            'post_weak_topic_improvement': 78.0,
            'post_consistency_rate': 88.0,
            'post_mock_exam_score': 85.0,
            'post_stress_level': 3,
            'student_feedback': "Sample Benchmark Data: Study hours increased sustainably with reduced academic anxiety.",
            'recorded_date': 'Sample Demo'
        }

    # Calculate percentage improvements
    hours_diff = analysis_record['post_weekly_study_hours'] - analysis_record['baseline_weekly_study_hours']
    topics_diff = analysis_record['post_topics_per_week'] - analysis_record['baseline_topics_per_week']
    weak_diff = analysis_record['post_weak_topic_improvement'] - analysis_record['baseline_weak_topic_improvement']
    consistency_diff = analysis_record['post_consistency_rate'] - analysis_record['baseline_consistency_rate']
    quiz_diff = analysis_record['post_mock_exam_score'] - analysis_record['baseline_mock_exam_score']
    stress_diff = analysis_record['baseline_stress_level'] - analysis_record['post_stress_level'] # Stress reduction is positive

    improvements = {
        'hours_diff': f"+{hours_diff:.1f} hrs/week",
        'topics_diff': f"+{topics_diff} topics/week",
        'weak_diff': f"+{weak_diff:.1f}% mastery",
        'consistency_diff': f"+{consistency_diff:.1f}% consistency",
        'quiz_diff': f"+{quiz_diff:.1f} marks gain",
        'stress_diff': f"-{stress_diff} points reduction"
    }

    return render_template('analysis.html', record=analysis_record, improvements=improvements)
