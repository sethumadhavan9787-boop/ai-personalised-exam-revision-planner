import os
import unittest
from datetime import date
from database.database import init_db, get_db_connection, seed_demo_student
from ai.planner import AIRevisionPlanner
from ai.prompt_engine import PromptEngine
from ai.comparison import AIComparator
from validation.timetable_validator import TimetableValidator

class TestAIExamRevisionPlanner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize test database
        init_db()
        seed_demo_student(user_id=1)

    def test_01_database_and_demo_seed(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM student_profiles WHERE user_id = 1")
        profile = cursor.fetchone()
        self.assertIsNotNone(profile)
        self.assertEqual(profile['full_name'], "Alex R. Sharma")

        cursor.execute("SELECT COUNT(*) as count FROM subjects WHERE user_id = 1")
        subj_count = cursor.fetchone()['count']
        self.assertGreaterEqual(subj_count, 5)

        cursor.execute("SELECT COUNT(*) as count FROM examinations WHERE user_id = 1")
        exam_count = cursor.fetchone()['count']
        self.assertGreaterEqual(exam_count, 5)

        cursor.execute("SELECT COUNT(*) as count FROM topics WHERE user_id = 1 AND is_weak = 1")
        weak_count = cursor.fetchone()['count']
        self.assertGreaterEqual(weak_count, 3)

        conn.close()

    def test_02_ai_plan_generation(self):
        planner = AIRevisionPlanner(user_id=1)
        plans = planner.generate_all_plans()

        self.assertEqual(len(plans), 3)
        self.assertEqual(plans[0]['plan_type'], 'plan_a_balanced')
        self.assertEqual(plans[1]['plan_type'], 'plan_b_weak_priority')
        self.assertEqual(plans[2]['plan_type'], 'plan_c_exam_deadline')

        # Check that study sessions were created in SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM study_sessions WHERE user_id = 1 AND plan_id = ?", (plans[0]['id'],))
        sessions_count = cursor.fetchone()['count']
        conn.close()

        self.assertGreater(sessions_count, 20)

    def test_03_timetable_validation(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM revision_plans WHERE user_id = 1 AND plan_type = 'plan_a_balanced'")
        plan = cursor.fetchone()
        conn.close()

        validator = TimetableValidator(plan['id'], user_id=1)
        result = validator.validate()
        validator.close()

        self.assertIn('overall_status', result)
        self.assertEqual(result['overall_status'], 'PASS')
        self.assertGreaterEqual(result['score'], 90)
        self.assertEqual(len(result['checks']), 7)

    def test_04_prompt_engine(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM student_profiles WHERE user_id = 1")
        profile = dict(cursor.fetchone())
        cursor.execute("SELECT * FROM subjects WHERE user_id = 1")
        subjects = [dict(s) for s in cursor.fetchall()]
        cursor.execute("SELECT * FROM topics WHERE user_id = 1")
        topics = [dict(t) for t in cursor.fetchall()]
        cursor.execute("SELECT e.*, s.name as subject_name FROM examinations e JOIN subjects s ON e.subject_id = s.id WHERE e.user_id = 1")
        exams = [dict(e) for e in cursor.fetchall()]
        conn.close()

        ctx = PromptEngine.format_student_context(profile, subjects, topics, exams)
        base = PromptEngine.get_baseline_prompt(ctx)
        imp = PromptEngine.get_improved_prompt(ctx)

        self.assertIn("Alex R. Sharma", imp)
        self.assertIn("Data Structures & Algorithms", imp)
        self.assertIn("Week | Date | Day", imp)
        self.assertIn("Create a 4-week study timetable", base)

    def test_05_ai_comparison(self):
        comparator = AIComparator(user_id=1)
        res = comparator.run_comparison(
            prompt="Create a revision plan",
            student_context={'student_name': 'Alex'},
            force_demo=True
        )

        self.assertIn('winner', res)
        self.assertIn('comparison_table', res)
        self.assertEqual(len(res['comparison_table']), 3)

if __name__ == '__main__':
    unittest.main()
