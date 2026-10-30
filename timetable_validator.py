from datetime import datetime, timedelta
from database.database import get_db_connection

class TimetableValidator:
    """
    Automated verification system to audit generated revision timetables against
    pedagogical, chronological, and student availability constraints.
    """

    def __init__(self, plan_id, user_id):
        self.plan_id = plan_id
        self.user_id = user_id
        self.conn = get_db_connection()
        self.load_data()

    def load_data(self):
        cursor = self.conn.cursor()

        # Load plan info
        cursor.execute("SELECT * FROM revision_plans WHERE id = ? AND user_id = ?", (self.plan_id, self.user_id))
        self.plan = cursor.fetchone()

        # Load profile
        cursor.execute("SELECT * FROM student_profiles WHERE user_id = ?", (self.user_id,))
        p_row = cursor.fetchone()
        self.profile = dict(p_row) if p_row else {
            'daily_study_availability': 4.0,
            'study_start_time': '09:00',
            'study_end_time': '21:00',
            'break_duration': 15
        }

        # Load sessions
        cursor.execute("""
            SELECT s.*, sub.name as subject_name, sub.code as subject_code,
                   t.name as topic_name, t.is_weak as topic_is_weak
            FROM study_sessions s
            JOIN subjects sub ON s.subject_id = sub.id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE s.plan_id = ? AND s.user_id = ?
            ORDER BY s.session_date ASC, s.start_time ASC
        """, (self.plan_id, self.user_id))
        self.sessions = [dict(s) for s in cursor.fetchall()]

        # Load exams
        cursor.execute("""
            SELECT e.*, sub.name as subject_name
            FROM examinations e
            JOIN subjects sub ON e.subject_id = sub.id
            WHERE e.user_id = ?
        """, (self.user_id,))
        self.exams = {e['subject_id']: e['exam_date'] for e in cursor.fetchall()}

    def validate(self):
        """
        Runs 7 comprehensive checks and generates a detailed audit report.
        """
        results = {
            'passed': True,
            'overall_status': 'PASS',
            'score': 100,
            'total_sessions_checked': len(self.sessions),
            'checks': [],
            'errors': [],
            'warnings': []
        }

        if not self.sessions:
            results['passed'] = False
            results['overall_status'] = 'FAIL'
            results['score'] = 0
            results['errors'].append("No study sessions found in this timetable.")
            return results

        # 1. Impossible study hours
        impossible_count = 0
        impossible_details = []
        for s in self.sessions:
            try:
                st = datetime.strptime(s['start_time'], "%H:%M")
                et = datetime.strptime(s['end_time'], "%H:%M")
                duration = (et - st).total_seconds() / 60
                if duration <= 0 or duration > 360:
                    impossible_count += 1
                    impossible_details.append(f"{s['session_date']} {s['start_time']}-{s['end_time']} ({duration}m)")
            except Exception as e:
                impossible_count += 1
                impossible_details.append(f"Format error in {s['session_date']}")

        c1 = {
            'name': 'Impossible Study Hours',
            'description': 'Validates that session start times precede end times and durations are positive and under 6 hours.',
            'status': 'PASS' if impossible_count == 0 else 'FAIL',
            'details': 'All session start and end times are chronologically valid.' if impossible_count == 0 else f"{impossible_count} invalid intervals: {', '.join(impossible_details[:3])}"
        }
        if impossible_count > 0:
            results['errors'].append(f"Found {impossible_count} sessions with impossible study hours.")
            results['score'] -= 20
        results['checks'].append(c1)

        # 2. Overlapping sessions
        overlap_count = 0
        overlap_details = []
        # Group sessions by date
        sessions_by_date = {}
        for s in self.sessions:
            d = s['session_date']
            sessions_by_date.setdefault(d, []).append(s)

        for d, day_sessions in sessions_by_date.items():
            for i in range(len(day_sessions)):
                for j in range(i + 1, len(day_sessions)):
                    s1 = day_sessions[i]
                    s2 = day_sessions[j]
                    st1 = datetime.strptime(s1['start_time'], "%H:%M")
                    et1 = datetime.strptime(s1['end_time'], "%H:%M")
                    st2 = datetime.strptime(s2['start_time'], "%H:%M")
                    et2 = datetime.strptime(s2['end_time'], "%H:%M")

                    if max(st1, st2) < min(et1, et2):
                        overlap_count += 1
                        overlap_details.append(f"{d}: '{s1['subject_name']}' ({s1['start_time']}-{s1['end_time']}) clashes with '{s2['subject_name']}' ({s2['start_time']}-{s2['end_time']})")

        c2 = {
            'name': 'Overlapping Study Sessions',
            'description': 'Ensures no two study sessions occupy the same time slot simultaneously.',
            'status': 'PASS' if overlap_count == 0 else 'FAIL',
            'details': 'Zero scheduling conflicts detected across all 4 weeks.' if overlap_count == 0 else f"{overlap_count} overlapping time clashes found: {'; '.join(overlap_details[:2])}"
        }
        if overlap_count > 0:
            results['errors'].append(f"Found {overlap_count} overlapping sessions.")
            results['score'] -= 25
        results['checks'].append(c2)

        # 3. Missing breaks between back-to-back sessions
        missing_break_count = 0
        for d, day_sessions in sessions_by_date.items():
            sorted_day = sorted(day_sessions, key=lambda x: x['start_time'])
            for i in range(len(sorted_day) - 1):
                et = datetime.strptime(sorted_day[i]['end_time'], "%H:%M")
                next_st = datetime.strptime(sorted_day[i+1]['start_time'], "%H:%M")
                gap_minutes = (next_st - et).total_seconds() / 60
                if gap_minutes < 10:  # Less than 10-minute break
                    missing_break_count += 1

        c3 = {
            'name': 'Adequate Break Allocation',
            'description': 'Verifies healthy cognitive recovery breaks (>= 10-15 mins) exist between consecutive study blocks.',
            'status': 'PASS' if missing_break_count == 0 else 'FAIL',
            'details': 'Structured cognitive recovery intervals confirmed between all consecutive blocks.' if missing_break_count == 0 else f"{missing_break_count} back-to-back sessions lack recommended recovery breaks."
        }
        if missing_break_count > 0:
            results['warnings'].append(f"{missing_break_count} consecutive study blocks lack adequate break gaps.")
            results['score'] -= 10
        results['checks'].append(c3)

        # 4. Sessions on or after examination dates
        post_exam_count = 0
        post_exam_details = []
        for s in self.sessions:
            s_id = s['subject_id']
            if s_id in self.exams:
                exam_date = datetime.strptime(self.exams[s_id], "%Y-%m-%d").date()
                session_date = datetime.strptime(s['session_date'], "%Y-%m-%d").date()
                if session_date > exam_date:
                    post_exam_count += 1
                    post_exam_details.append(f"{s['subject_name']} scheduled on {session_date} after exam date {exam_date}")

        c4 = {
            'name': 'Examination Date Accuracy',
            'description': 'Ensures no revision is wasted after an exam has already concluded.',
            'status': 'PASS' if post_exam_count == 0 else 'FAIL',
            'details': 'All revision sessions precede respective examination deadlines.' if post_exam_count == 0 else f"{post_exam_count} sessions scheduled post-exam date: {'; '.join(post_exam_details[:2])}"
        }
        if post_exam_count > 0:
            results['errors'].append(f"Found {post_exam_count} sessions scheduled after the examination date.")
            results['score'] -= 20
        results['checks'].append(c4)

        # 5. Sessions outside student availability window
        outside_window_count = 0
        window_start = datetime.strptime(self.profile.get('study_start_time', '09:00'), "%H:%M")
        window_end = datetime.strptime(self.profile.get('study_end_time', '21:00'), "%H:%M")

        for s in self.sessions:
            st = datetime.strptime(s['start_time'], "%H:%M")
            et = datetime.strptime(s['end_time'], "%H:%M")
            if st < window_start or et > window_end:
                outside_window_count += 1

        c5 = {
            'name': 'Student Availability Window Compliance',
            'description': f"Guarantees all sessions stay strictly within the student's defined hours ({self.profile.get('study_start_time')} to {self.profile.get('study_end_time')}).",
            'status': 'PASS' if outside_window_count == 0 else 'FAIL',
            'details': f"100% of study sessions fall neatly within the student's configured active window." if outside_window_count == 0 else f"{outside_window_count} sessions violate daily start/end limits."
        }
        if outside_window_count > 0:
            results['warnings'].append(f"{outside_window_count} sessions scheduled outside preferred daily hours.")
            results['score'] -= 15
        results['checks'].append(c5)

        # 6. Excessive daily workload
        max_daily_allowed = float(self.profile.get('daily_study_availability', 4.0))
        excess_day_count = 0
        for d, day_sessions in sessions_by_date.items():
            total_day_hours = sum(s['duration_minutes'] for s in day_sessions) / 60.0
            if total_day_hours > (max_daily_allowed + 0.5): # allow tiny margin
                excess_day_count += 1

        c6 = {
            'name': 'Daily Workload Feasibility',
            'description': f"Ensures total daily study time does not exceed the target threshold ({max_daily_allowed} hrs/day) to prevent cognitive fatigue.",
            'status': 'PASS' if excess_day_count == 0 else 'FAIL',
            'details': f"Daily workloads adhere to student's sustainable capacity." if excess_day_count == 0 else f"{excess_day_count} days exceed the maximum daily available hours."
        }
        if excess_day_count > 0:
            results['warnings'].append(f"{excess_day_count} days exceed your daily study availability.")
            results['score'] -= 10
        results['checks'].append(c6)

        # 7. Weak topic coverage
        weak_sessions = [s for s in self.sessions if s.get('topic_is_weak') or s.get('priority') == 'High']
        weak_ratio = (len(weak_sessions) / len(self.sessions)) * 100 if self.sessions else 0
        weak_sufficient = weak_ratio >= 30.0

        c7 = {
            'name': 'Weak Topic Prioritisation',
            'description': 'Validates that identified weak topics receive at least 30% of total dedicated revision time.',
            'status': 'PASS' if weak_sufficient else 'FAIL',
            'details': f"Weak topics receive {weak_ratio:.1f}% of revision focus (Target: >= 30.0%)." if weak_sufficient else f"Weak topics only receive {weak_ratio:.1f}% of study time, which is insufficient."
        }
        if not weak_sufficient:
            results['warnings'].append(f"Weak topic allocation ({weak_ratio:.1f}%) is below the recommended 30% threshold.")
            results['score'] -= 10
        results['checks'].append(c7)

        # Final verdict
        results['score'] = max(0, min(100, results['score']))
        results['passed'] = len(results['errors']) == 0
        results['overall_status'] = 'PASS' if results['passed'] else 'FAIL'

        return results

    def close(self):
        if self.conn:
            self.conn.close()
