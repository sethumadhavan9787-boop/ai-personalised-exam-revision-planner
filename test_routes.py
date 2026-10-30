import unittest
from app import create_app
from database.database import init_db, seed_demo_student
from ai.planner import AIRevisionPlanner

class TestRoutesAndExports(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Seed demo student
        init_db()
        seed_demo_student(user_id=1)
        planner = AIRevisionPlanner(user_id=1)
        planner.generate_all_plans()

    def test_demo_login_flow(self):
        response = self.client.get('/demo-login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex R. Sharma", response.data)

    def test_dashboard_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Total Subjects", response.data)
        self.assertIn(b"Weekly Hours", response.data)
        self.assertIn(b"Timetable Validation Audit", response.data)

    def test_profile_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex R. Sharma", response.data)
        self.assertIn(b"Imperial Institute of Technology", response.data)

    def test_subjects_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/subjects/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Data Structures &amp; Algorithms", response.data)
        self.assertIn(b"Operating Systems", response.data)

    def test_exams_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/exams/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Upcoming Examinations", response.data)

    def test_planner_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/planner/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Plan A: Balanced Revision Plan", response.data)
        self.assertIn(b"Plan B: Weak Topic Priority Plan", response.data)
        self.assertIn(b"Plan C: Exam Deadline Priority Plan", response.data)
        self.assertIn(b"Automated Timetable Verification Report", response.data)

    def test_comparison_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/comparison/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ChatGPT (OpenAI)", response.data)
        self.assertIn(b"Google Gemini", response.data)
        self.assertIn(b"Claude (Anthropic)", response.data)

    def test_timetable_page(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        response = self.client.get('/timetable/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Weekly Revision Timetable", response.data)
        self.assertIn(b"Google Calendar (.ICS)", response.data)
        self.assertIn(b"Notion Database (.CSV)", response.data)

    def test_calendar_ics_export(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        # Get plan ID
        planner = AIRevisionPlanner(user_id=1)
        plans = planner.generate_all_plans()
        plan_id = plans[0]['id']

        response = self.client.get(f'/exports/calendar/ics/{plan_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/calendar')
        self.assertIn(b"BEGIN:VCALENDAR", response.data)
        self.assertIn(b"BEGIN:VEVENT", response.data)
        self.assertIn(b"END:VCALENDAR", response.data)

    def test_notion_csv_export(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        planner = AIRevisionPlanner(user_id=1)
        plans = planner.generate_all_plans()
        plan_id = plans[0]['id']

        response = self.client.get(f'/exports/notion/csv/{plan_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b"Session Name,Subject,Code,Topic", response.data)

    def test_progress_and_analysis_pages(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        resp_prog = self.client.get('/progress/')
        self.assertEqual(resp_prog.status_code, 200)
        self.assertIn(b"Weekly Progress Tracker", resp_prog.data)

        resp_ana = self.client.get('/analysis/')
        self.assertEqual(resp_ana.status_code, 200)
        self.assertIn(b"Before vs After Analysis", resp_ana.data)

    def test_prompts_and_responsible_ai(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'demo_student'

        resp_prompts = self.client.get('/prompts/')
        self.assertEqual(resp_prompts.status_code, 200)
        self.assertIn(b"Prompt Engineering Library", resp_prompts.data)

        resp_ethics = self.client.get('/responsible-ai/')
        self.assertEqual(resp_ethics.status_code, 200)
        self.assertIn(b"Responsible AI", resp_ethics.data)

if __name__ == '__main__':
    unittest.main()
