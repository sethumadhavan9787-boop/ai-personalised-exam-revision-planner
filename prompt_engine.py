class PromptEngine:
    """
    Prompt engineering engine for generating baseline and improved prompts,
    custom parameter interpolation, and pedagogical guardrails.
    """

    BASELINE_PROMPT_TEMPLATE = (
        "Create a 4-week study timetable for a student based on subjects, examination dates, "
        "available hours and weak topics."
    )

    IMPROVED_PROMPT_TEMPLATE = (
        "You are an expert AI academic planning assistant. Create a realistic and personalised "
        "4-week examination revision timetable based on the student's subjects, examination dates, "
        "available study hours, weak topics and strong topics.\n\n"
        "Student Context:\n"
        "- Name: {student_name} ({year_of_study}, {department})\n"
        "- Subjects: {subjects_list}\n"
        "- Upcoming Examinations: {exams_list}\n"
        "- Weekly Available Hours: {weekly_hours} hours ({daily_hours} hours/day)\n"
        "- Active Study Window: {start_time} to {end_time}\n"
        "- Weak Topics (Must Prioritise): {weak_topics}\n"
        "- Strong Topics: {strong_topics}\n"
        "- Learning Style: {learning_style}\n\n"
        "Guidelines & Constraints:\n"
        "1. Prioritise weak topics and upcoming examinations.\n"
        "2. Include reasonable breaks ({break_duration} mins), revision sessions and practice tests.\n"
        "3. Never schedule overlapping sessions or exceed the student's available hours.\n"
        "4. Return the result in a structured table with these columns:\n"
        "   Week | Date | Day | Subject | Topic | Start Time | End Time | Duration | Priority | Activity\n\n"
        "5. After generating the timetable, verify all dates, available hours, study durations, "
        "breaks and subject priorities. Explain any scheduling limitations."
    )

    @classmethod
    def format_student_context(cls, profile, subjects, topics, exams):
        """Format database entities into clean strings for prompt interpolation"""
        if profile is not None:
            try:
                profile = dict(profile)
            except Exception:
                pass

        student_name = profile.get('full_name', 'Student') if profile else 'Student'
        year_of_study = profile.get('year_of_study', 'College Student') if profile else 'College Student'
        department = profile.get('department', 'General') if profile else 'General'
        weekly_hours = profile.get('weekly_free_hours', 20.0) if profile else 20.0
        daily_hours = profile.get('daily_study_availability', 4.0) if profile else 4.0
        start_time = profile.get('study_start_time', '09:00') if profile else '09:00'
        end_time = profile.get('study_end_time', '21:00') if profile else '21:00'
        break_duration = profile.get('break_duration', 15) if profile else 15
        learning_style = profile.get('learning_style', 'Active Problem Solving') if profile else 'Active Problem Solving'

        subjects_list = ", ".join([f"{s['name']} (Difficulty: {s.get('difficulty_level', 3)}/5)" for s in subjects]) or "None listed"

        weak_list = [t['name'] for t in topics if t.get('is_weak')]
        weak_topics = ", ".join(weak_list) if weak_list else "None specified"

        strong_list = [t['name'] for t in topics if t.get('is_strong')]
        strong_topics = ", ".join(strong_list) if strong_list else "None specified"

        exam_items = []
        for e in exams:
            s_name = e.get('subject_name', 'Subject')
            e_date = e.get('exam_date', 'Upcoming')
            exam_items.append(f"{s_name} on {e_date}")
        exams_list = "; ".join(exam_items) if exam_items else "Ongoing Semester"

        return {
            'student_name': student_name,
            'year_of_study': year_of_study,
            'department': department,
            'weekly_hours': weekly_hours,
            'daily_hours': daily_hours,
            'start_time': start_time,
            'end_time': end_time,
            'break_duration': break_duration,
            'learning_style': learning_style,
            'subjects_list': subjects_list,
            'weak_topics': weak_topics,
            'strong_topics': strong_topics,
            'exams_list': exams_list
        }

    @classmethod
    def get_baseline_prompt(cls, context=None):
        return cls.BASELINE_PROMPT_TEMPLATE

    @classmethod
    def get_improved_prompt(cls, context):
        return cls.IMPROVED_PROMPT_TEMPLATE.format(**context)
