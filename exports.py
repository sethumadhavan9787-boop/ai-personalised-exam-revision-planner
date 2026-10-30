import csv
import io
from datetime import datetime, date, timezone
from flask import Blueprint, send_file, Response, request, session, flash, redirect, url_for
from database.database import get_db_connection
from config import Config

exports_bp = Blueprint('exports', __name__, url_prefix='/exports')

def get_current_user_id():
    return session.get('user_id', 1)

@exports_bp.route('/calendar/ics/<int:plan_id>')
def export_ics(plan_id):
    """Generates standard RFC 5545 iCalendar (.ics) file compatible with Google Calendar, Outlook, and Apple Calendar."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM revision_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
    plan = cursor.fetchone()
    if not plan:
        flash("Revision plan not found.", "danger")
        return redirect(url_for('timetable.view_timetable'))

    cursor.execute("""
        SELECT s.*, sub.name as subject_name, sub.code as subject_code,
               t.name as topic_name
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE s.plan_id = ? AND s.user_id = ?
        ORDER BY s.session_date ASC, s.start_time ASC
    """, (plan_id, user_id))
    sessions = cursor.fetchall()
    conn.close()

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI Personalised Exam Revision Planner//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{plan['plan_name']} - AI Revision Schedule",
        "X-WR-TIMEZONE:UTC"
    ]

    now_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    for s in sessions:
        # Format date & times
        date_str = s['session_date'].replace('-', '')
        start_time_str = s['start_time'].replace(':', '') + '00'
        end_time_str = s['end_time'].replace(':', '') + '00'

        dtstart = f"{date_str}T{start_time_str}"
        dtend = f"{date_str}T{end_time_str}"
        uid = f"session_{s['id']}_{s['session_date']}@aiexamplanner.local"

        summary = f"[{s['subject_code'] or s['subject_name']}] {s['topic_name'] or 'Revision'} - {s['activity_type']}"
        desc = (
            f"Subject: {s['subject_name']}\\n"
            f"Topic: {s['topic_name'] or 'Comprehensive'}\\n"
            f"Activity: {s['activity_type']}\\n"
            f"Priority: {s['priority']}\\n"
            f"Status: {s['status']}\\n"
            f"Notes: {s['notes'] or 'Stay focused with structured active recall.'}"
        )

        prio_val = "1" if s['priority'] == 'High' else ("5" if s['priority'] == 'Medium' else "9")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"SUMMARY:{summary}",
            f"DESCRIPTION:{desc}",
            f"PRIORITY:{prio_val}",
            f"STATUS:CONFIRMED",
            f"CATEGORIES:Exam Revision,{s['subject_name']}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(lines)

    filename = f"AI_Revision_Plan_{plan['plan_type']}.ics"
    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@exports_bp.route('/notion/csv/<int:plan_id>')
def export_notion_csv(plan_id):
    """Generates a structured CSV file formatted for direct import into Notion as a database table."""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM revision_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
    plan = cursor.fetchone()
    if not plan:
        flash("Revision plan not found.", "danger")
        return redirect(url_for('timetable.view_timetable'))

    cursor.execute("""
        SELECT s.*, sub.name as subject_name, sub.code as subject_code,
               t.name as topic_name
        FROM study_sessions s
        JOIN subjects sub ON s.subject_id = sub.id
        LEFT JOIN topics t ON s.topic_id = t.id
        WHERE s.plan_id = ? AND s.user_id = ?
        ORDER BY s.session_date ASC, s.start_time ASC
    """, (plan_id, user_id))
    sessions = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Notion-friendly headers
    headers = [
        "Session Name", "Subject", "Code", "Topic", "Date", "Day",
        "Start Time", "End Time", "Duration (Minutes)", "Activity Type",
        "Priority", "Status", "Week", "Notes"
    ]
    writer.writerow(headers)

    for s in sessions:
        session_name = f"[{s['subject_code'] or s['subject_name']}] {s['topic_name'] or 'Revision'}"
        writer.writerow([
            session_name,
            s['subject_name'],
            s['subject_code'] or 'N/A',
            s['topic_name'] or 'Comprehensive Exam Review',
            s['session_date'],
            s['day_of_week'],
            s['start_time'],
            s['end_time'],
            s['duration_minutes'],
            s['activity_type'],
            s['priority'],
            s['status'],
            f"Week {s['week_number']}",
            s['notes'] or ''
        ])

    csv_data = output.getvalue()
    filename = f"Notion_AI_Revision_Plan_{plan['plan_type']}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
