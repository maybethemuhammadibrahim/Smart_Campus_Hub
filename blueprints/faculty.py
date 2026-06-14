from datetime import date

from flask import (
    Blueprint, flash, jsonify, redirect, render_template,
    request, session, url_for,
)
from mysql.connector import Error as MySQLError

from db_connector import execute_query
from decorators import login_required, role_required

faculty_bp = Blueprint('faculty', __name__)


# ── helpers ──────────────────────────────────────────────────

def _faculty_courses(faculty_id):
    """Return sections assigned to the given faculty member.

    Uses course_sections as the base table. Returns cs.section_id aliased
    as 'course_id' so that all URL params and template references continue
    to work without change.
    """
    return execute_query(
        """SELECT cs.section_id AS course_id,
                  c.course_code, c.course_name, c.credit_hours,
                  cs.section_code, sm.name AS semester_name,
                  cs.max_capacity,
                  COUNT(e.enrollment_id) AS enrolled_count
           FROM course_sections cs
           JOIN courses c ON cs.course_id = c.course_id
           JOIN semesters sm ON cs.semester_id = sm.semester_id
           LEFT JOIN enrollments e ON cs.section_id = e.section_id AND e.status = 'active'
           WHERE cs.faculty_id = %s
           GROUP BY cs.section_id, c.course_code, c.course_name,
                    c.credit_hours, cs.section_code, sm.name, cs.max_capacity
           ORDER BY c.course_code, cs.section_code""",
        (faculty_id,),
    )


def _owns_course(faculty_id, course_id):
    """Check whether the faculty owns the given section (course_id is section_id)."""
    row = execute_query(
        "SELECT section_id FROM course_sections WHERE section_id=%s AND faculty_id=%s",
        (course_id, faculty_id),
    )
    return bool(row)


def _get_faculty_info(faculty_id):
    rows = execute_query("SELECT * FROM faculty WHERE faculty_id=%s", (faculty_id,))
    return rows[0] if rows else {}


def _compute_letter_grade(marks):
    """Return (letter_grade, grade_points) for a given marks value."""
    if marks >= 90: return ('A',  4.00)
    if marks >= 85: return ('A-', 3.70)
    if marks >= 80: return ('B+', 3.30)
    if marks >= 75: return ('B',  3.00)
    if marks >= 70: return ('B-', 2.70)
    if marks >= 65: return ('C+', 2.30)
    if marks >= 60: return ('C',  2.00)
    return ('F', 0.00)


# ── dashboard ────────────────────────────────────────────────

@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty')
def dashboard():
    fid = session['entity_id']
    faculty = _get_faculty_info(fid)
    courses = _faculty_courses(fid)
    total_students = sum((c.get('enrolled_count') or 0) for c in courses)

    # Average attendance across all sections
    avg_attendance = execute_query(
        """SELECT ROUND(AVG(att.attendance_percentage), 1) AS avg_att
           FROM v_attendance_summary att
           JOIN enrollments e ON att.enrollment_id = e.enrollment_id
           JOIN course_sections cs ON e.section_id = cs.section_id
           WHERE cs.faculty_id = %s AND e.status = 'active'""",
        (fid,),
    )
    avg_att = avg_attendance[0]['avg_att'] if avg_attendance and avg_attendance[0]['avg_att'] else 0

    # Average grade across all sections
    avg_grade = execute_query(
        """SELECT ROUND(AVG(g.marks_obtained), 1) AS avg_marks
           FROM grades g
           JOIN enrollments e ON g.enrollment_id = e.enrollment_id
           JOIN course_sections cs ON e.section_id = cs.section_id
           WHERE cs.faculty_id = %s AND e.status = 'active'
             AND g.marks_obtained IS NOT NULL""",
        (fid,),
    )
    avg_marks = avg_grade[0]['avg_marks'] if avg_grade and avg_grade[0]['avg_marks'] else 0

    # Recent activity (last 10 attendance/grade entries)
    recent_activity = execute_query(
        """(SELECT 'attendance' AS type,
                  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                  c.course_code,
                  a.status AS detail,
                  a.class_date AS activity_date
           FROM attendance a
           JOIN enrollments e ON a.enrollment_id = e.enrollment_id
           JOIN students s ON e.student_id = s.student_id
           JOIN course_sections cs ON e.section_id = cs.section_id
           JOIN courses c ON cs.course_id = c.course_id
           WHERE cs.faculty_id = %s
           ORDER BY a.class_date DESC LIMIT 5)
          UNION ALL
          (SELECT 'grade' AS type,
                  CONCAT(s.first_name, ' ', s.last_name) AS student_name,
                  c.course_code,
                  CONCAT(g.marks_obtained, '/100 — ', IFNULL(g.letter_grade, 'N/A')) AS detail,
                  e.enrolled_at AS activity_date
           FROM grades g
           JOIN enrollments e ON g.enrollment_id = e.enrollment_id
           JOIN students s ON e.student_id = s.student_id
           JOIN course_sections cs ON e.section_id = cs.section_id
           JOIN courses c ON cs.course_id = c.course_id
           WHERE cs.faculty_id = %s AND g.marks_obtained > 0
           ORDER BY e.enrolled_at DESC LIMIT 5)
          ORDER BY activity_date DESC LIMIT 10""",
        (fid, fid),
    )

    return render_template(
        'faculty/dashboard.html',
        faculty=faculty,
        courses=courses,
        total_students=total_students,
        avg_attendance=avg_att,
        avg_marks=avg_marks,
        recent_activity=recent_activity,
    )


# ── my courses ───────────────────────────────────────────────

@faculty_bp.route('/my-courses')
@login_required
@role_required('faculty')
def my_courses():
    fid = session['entity_id']
    courses = _faculty_courses(fid)
    return render_template('faculty/my_courses.html', courses=courses)


# ── roster ───────────────────────────────────────────────────

@faculty_bp.route('/roster', defaults={'course_id': None})
@faculty_bp.route('/roster/<int:course_id>')
@login_required
@role_required('faculty')
def roster(course_id):
    fid = session['entity_id']
    courses = _faculty_courses(fid)

    if course_id is None and courses:
        course_id = courses[0]['course_id']

    if not course_id:
        return render_template(
            'faculty/roster.html',
            students=[], courses=courses,
            selected_course=None, course_name='No Course Selected',
            summary={},
        )

    if not _owns_course(fid, course_id):
        flash('You do not have access to this course roster.', 'danger')
        return redirect(url_for('faculty.my_courses'))

    students = execute_query(
        """SELECT s.student_id, s.first_name, s.last_name, s.email,
                  e.enrollment_id, e.enrolled_at,
                  att.attendance_percentage,
                  g.letter_grade, g.marks_obtained
           FROM enrollments e
           JOIN students s ON e.student_id = s.student_id
           LEFT JOIN v_attendance_summary att ON att.enrollment_id = e.enrollment_id
           LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
           WHERE e.section_id = %s AND e.status = 'active'
           ORDER BY s.first_name, s.last_name""",
        (course_id,),
    )
    course = execute_query(
        """SELECT c.course_name, cs.section_code
           FROM course_sections cs
           JOIN courses c ON cs.course_id = c.course_id
           WHERE cs.section_id = %s""",
        (course_id,),
    )

    # Summary stats
    total = len(students)
    graded = [s for s in students if s.get('marks_obtained') is not None and s['marks_obtained'] > 0]
    avg_marks = round(sum(s['marks_obtained'] for s in graded) / len(graded), 1) if graded else 0
    att_values = [s['attendance_percentage'] for s in students if s.get('attendance_percentage') is not None]
    avg_att = round(sum(att_values) / len(att_values), 1) if att_values else 0

    summary = {
        'total': total,
        'graded': len(graded),
        'avg_marks': avg_marks,
        'avg_attendance': avg_att,
    }

    return render_template(
        'faculty/roster.html',
        students=students,
        courses=courses,
        selected_course=course_id,
        course_name=course[0]['course_name'] if course else 'Course',
        summary=summary,
    )


# ── mark attendance ──────────────────────────────────────────

@faculty_bp.route('/attendance', defaults={'course_id': None})
@faculty_bp.route('/attendance/<int:course_id>')
@login_required
@role_required('faculty')
def mark_attendance(course_id):
    fid = session['entity_id']
    courses = _faculty_courses(fid)

    if course_id is None and courses:
        course_id = courses[0]['course_id']

    students = []
    if course_id:
        if not _owns_course(fid, course_id):
            flash('You do not have access to this course.', 'danger')
            return redirect(url_for('faculty.my_courses'))

        students = execute_query(
            """SELECT e.enrollment_id, s.first_name, s.last_name
               FROM enrollments e
               JOIN students s ON e.student_id = s.student_id
               WHERE e.section_id=%s AND e.status='active'
               ORDER BY s.first_name, s.last_name""",
            (course_id,),
        )

    return render_template(
        'faculty/mark_attendance.html',
        courses=courses,
        students=students,
        selected_course=course_id,
        today=date.today().isoformat(),
    )


@faculty_bp.route('/attendance/submit', methods=['POST'])
@login_required
@role_required('faculty')
def submit_attendance():
    fid = session['entity_id']
    marker_user_id = session['user_id']

    try:
        course_id = int(request.form.get('course_id', '0'))
    except (ValueError, TypeError):
        flash('Please select a valid course.', 'danger')
        return redirect(url_for('faculty.mark_attendance'))

    attendance_date = request.form.get('attendance_date', '').strip()
    if not attendance_date:
        flash('Attendance date is required.', 'danger')
        return redirect(url_for('faculty.mark_attendance', course_id=course_id))

    if not _owns_course(fid, course_id):
        flash('You do not have access to submit attendance for this course.', 'danger')
        return redirect(url_for('faculty.my_courses'))

    enrollments = execute_query(
        "SELECT enrollment_id FROM enrollments WHERE section_id=%s AND status='active'",
        (course_id,),
    )

    if not enrollments:
        flash('No active students found for the selected course.', 'warning')
        return redirect(url_for('faculty.mark_attendance', course_id=course_id))

    marked = 0
    for row in enrollments:
        enrollment_id = row['enrollment_id']
        status = request.form.get(f'status_{enrollment_id}', 'present')
        if status not in ('present', 'absent', 'late'):
            status = 'present'

        try:
            execute_query(
                """INSERT INTO attendance (enrollment_id, class_date, status, marked_by)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE
                     status = VALUES(status),
                     marked_by = VALUES(marked_by)""",
                (enrollment_id, attendance_date, status, marker_user_id),
                fetch=False,
            )
            marked += 1
        except MySQLError as e:
            flash(f'Error saving attendance: {str(e)}', 'danger')
            return redirect(url_for('faculty.mark_attendance', course_id=course_id))

    flash(f'Attendance submitted for {marked} student(s).', 'success')
    return redirect(url_for('faculty.mark_attendance', course_id=course_id))


# ── attendance history ───────────────────────────────────────

@faculty_bp.route('/attendance/history', defaults={'course_id': None})
@faculty_bp.route('/attendance/history/<int:course_id>')
@login_required
@role_required('faculty')
def attendance_history(course_id):
    fid = session['entity_id']
    courses = _faculty_courses(fid)

    if course_id is None and courses:
        course_id = courses[0]['course_id']

    records = []
    dates = []
    if course_id:
        if not _owns_course(fid, course_id):
            flash('You do not have access to this course.', 'danger')
            return redirect(url_for('faculty.my_courses'))

        records = execute_query(
            """SELECT a.class_date, a.status,
                      s.first_name, s.last_name, e.enrollment_id
               FROM attendance a
               JOIN enrollments e ON a.enrollment_id = e.enrollment_id
               JOIN students s ON e.student_id = s.student_id
               WHERE e.section_id = %s AND e.status = 'active'
               ORDER BY a.class_date DESC, s.first_name""",
            (course_id,),
        )

        dates = execute_query(
            """SELECT DISTINCT a.class_date,
                      COUNT(CASE WHEN a.status = 'present' THEN 1 END) AS present_count,
                      COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS absent_count,
                      COUNT(CASE WHEN a.status = 'late' THEN 1 END) AS late_count,
                      COUNT(*) AS total
               FROM attendance a
               JOIN enrollments e ON a.enrollment_id = e.enrollment_id
               WHERE e.section_id = %s AND e.status = 'active'
               GROUP BY a.class_date
               ORDER BY a.class_date DESC""",
            (course_id,),
        )

    return render_template(
        'faculty/attendance_history.html',
        courses=courses,
        selected_course=course_id,
        records=records,
        dates=dates,
    )


# ── enter grades ─────────────────────────────────────────────

@faculty_bp.route('/grades', defaults={'course_id': None})
@faculty_bp.route('/grades/<int:course_id>')
@login_required
@role_required('faculty')
def enter_grades(course_id):
    fid = session['entity_id']
    courses = _faculty_courses(fid)

    if course_id is None and courses:
        course_id = courses[0]['course_id']

    students = []
    course_name = 'No Course Selected'

    if course_id:
        if not _owns_course(fid, course_id):
            flash('You do not have access to this course.', 'danger')
            return redirect(url_for('faculty.my_courses'))

        students = execute_query(
            """SELECT e.enrollment_id, s.first_name, s.last_name,
                      g.marks_obtained AS marks, g.letter_grade, g.grade_points
               FROM enrollments e
               JOIN students s ON e.student_id = s.student_id
               LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
               WHERE e.section_id = %s AND e.status = 'active'
               ORDER BY s.first_name, s.last_name""",
            (course_id,),
        )
        course = execute_query(
            """SELECT c.course_name, cs.section_code
               FROM course_sections cs
               JOIN courses c ON cs.course_id = c.course_id
               WHERE cs.section_id = %s""",
            (course_id,),
        )
        if course:
            course_name = course[0]['course_name'] + ' (Sec ' + (course[0].get('section_code') or 'A') + ')'

    return render_template(
        'faculty/enter_grades.html',
        students=students,
        course_id=course_id,
        course_name=course_name,
        courses=courses,
        selected_course=course_id,
    )


@faculty_bp.route('/grades/save', methods=['POST'])
@login_required
@role_required('faculty')
def save_grades():
    fid = session['entity_id']

    try:
        course_id = int(request.form.get('course_id', '0'))
    except (ValueError, TypeError):
        flash('Invalid course selected.', 'danger')
        return redirect(url_for('faculty.enter_grades'))

    if not _owns_course(fid, course_id):
        flash('You do not have access to save grades for this course.', 'danger')
        return redirect(url_for('faculty.my_courses'))

    enrollments = execute_query(
        "SELECT enrollment_id FROM enrollments WHERE section_id=%s AND status='active'",
        (course_id,),
    )

    updated = 0
    errors = 0
    for row in enrollments:
        enrollment_id = row['enrollment_id']
        marks_raw = request.form.get(f'marks_{enrollment_id}')
        if marks_raw in (None, ''):
            continue

        try:
            marks = float(marks_raw)
        except (ValueError, TypeError):
            errors += 1
            continue

        # Clamp to valid range
        marks = max(0.0, min(100.0, marks))

        letter, points = _compute_letter_grade(marks)

        try:
            # Check if grade row already exists (created by SP during enrollment)
            existing = execute_query(
                "SELECT grade_id FROM grades WHERE enrollment_id = %s",
                (enrollment_id,),
            )
            if existing:
                # UPDATE existing grade row
                execute_query(
                    """UPDATE grades
                       SET marks_obtained = %s, total_marks = 100,
                           letter_grade = %s, grade_points = %s
                       WHERE enrollment_id = %s""",
                    (marks, letter, points, enrollment_id),
                    fetch=False,
                )
            else:
                # INSERT new grade row
                execute_query(
                    """INSERT INTO grades
                           (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points)
                       VALUES (%s, %s, 100, %s, %s)""",
                    (enrollment_id, marks, letter, points),
                    fetch=False,
                )
            updated += 1
        except MySQLError as e:
            errors += 1
            flash(f'Error saving grade: {str(e)}', 'danger')

    # CGPA write-back REMOVED — cgpa is now computed via v_student_cgpa view

    msg = f'Grades saved for {updated} student(s).'
    if errors:
        msg += f' {errors} error(s) occurred.'
        flash(msg, 'warning')
    else:
        flash(msg, 'success')
    return redirect(url_for('faculty.enter_grades', course_id=course_id))


# ── course analytics ─────────────────────────────────────────

@faculty_bp.route('/analytics', defaults={'course_id': None})
@faculty_bp.route('/analytics/<int:course_id>')
@login_required
@role_required('faculty')
def analytics(course_id):
    fid = session['entity_id']
    courses = _faculty_courses(fid)

    if course_id is None and courses:
        course_id = courses[0]['course_id']

    stats = {}
    grade_dist = []
    top_students = []
    at_risk = []

    if course_id:
        if not _owns_course(fid, course_id):
            flash('You do not have access to this course.', 'danger')
            return redirect(url_for('faculty.my_courses'))

        # Overall stats
        stats_row = execute_query(
            """SELECT
                   COUNT(e.enrollment_id) AS total_students,
                   ROUND(AVG(g.marks_obtained), 1) AS avg_marks,
                   MAX(g.marks_obtained) AS highest,
                   MIN(g.marks_obtained) AS lowest,
                   ROUND(AVG(att.attendance_percentage), 1) AS avg_attendance
               FROM enrollments e
               LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
               LEFT JOIN v_attendance_summary att ON att.enrollment_id = e.enrollment_id
               WHERE e.section_id = %s AND e.status = 'active'""",
            (course_id,),
        )
        stats = stats_row[0] if stats_row else {}

        # Grade distribution
        grade_dist = execute_query(
            """SELECT g.letter_grade, COUNT(*) AS count
               FROM grades g
               JOIN enrollments e ON g.enrollment_id = e.enrollment_id
               WHERE e.section_id = %s AND e.status = 'active'
                 AND g.letter_grade IS NOT NULL
               GROUP BY g.letter_grade
               ORDER BY FIELD(g.letter_grade, 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'F')""",
            (course_id,),
        )

        # Top performers
        top_students = execute_query(
            """SELECT s.first_name, s.last_name, g.marks_obtained, g.letter_grade
               FROM enrollments e
               JOIN students s ON e.student_id = s.student_id
               JOIN grades g ON e.enrollment_id = g.enrollment_id
               WHERE e.section_id = %s AND e.status = 'active'
                 AND g.marks_obtained IS NOT NULL
               ORDER BY g.marks_obtained DESC LIMIT 5""",
            (course_id,),
        )

        # At-risk students (low attendance or failing)
        at_risk = execute_query(
            """SELECT s.first_name, s.last_name, s.email,
                      COALESCE(att.attendance_percentage, 0) AS attendance,
                      COALESCE(g.marks_obtained, 0) AS marks,
                      g.letter_grade
               FROM enrollments e
               JOIN students s ON e.student_id = s.student_id
               LEFT JOIN v_attendance_summary att ON att.enrollment_id = e.enrollment_id
               LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
               WHERE e.section_id = %s AND e.status = 'active'
                 AND (
                     (att.attendance_percentage IS NOT NULL AND att.attendance_percentage < 75)
                     OR g.letter_grade = 'F'
                     OR (g.marks_obtained IS NOT NULL AND g.marks_obtained < 60)
                 )
               ORDER BY COALESCE(g.marks_obtained, 0) ASC""",
            (course_id,),
        )

    course_info = execute_query(
        """SELECT c.course_name, c.course_code, cs.section_code
           FROM course_sections cs
           JOIN courses c ON cs.course_id = c.course_id
           WHERE cs.section_id = %s""",
        (course_id,),
    ) if course_id else []

    return render_template(
        'faculty/analytics.html',
        courses=courses,
        selected_course=course_id,
        course_info=course_info[0] if course_info else {},
        stats=stats,
        grade_dist=grade_dist,
        top_students=top_students,
        at_risk=at_risk,
    )


# ── faculty profile ──────────────────────────────────────────

@faculty_bp.route('/profile')
@login_required
@role_required('faculty')
def profile():
    fid = session['entity_id']
    faculty = _get_faculty_info(fid)
    courses = _faculty_courses(fid)
    total_students = sum((c.get('enrolled_count') or 0) for c in courses)

    return render_template(
        'faculty/profile.html',
        faculty=faculty,
        courses=courses,
        total_students=total_students,
    )


@faculty_bp.route('/change-password', methods=['POST'])
@login_required
@role_required('faculty')
def change_password():
    user_id = session['user_id']

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not all([current_password, new_password, confirm_password]):
        flash('All password fields are required.', 'danger')
        return redirect(url_for('faculty.profile'))

    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('faculty.profile'))

    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'danger')
        return redirect(url_for('faculty.profile'))

    # Verify current password (support both hashed and plaintext — same as auth.py)
    from werkzeug.security import check_password_hash as _check_hash
    user = execute_query("SELECT password FROM users WHERE user_id=%s", (user_id,))
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('faculty.profile'))

    stored_pw = user[0]['password']
    password_ok = False
    try:
        password_ok = _check_hash(stored_pw, current_password)
    except Exception:
        pass
    if not password_ok:
        password_ok = (stored_pw == current_password)

    if not password_ok:
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('faculty.profile'))

    # Store new password (plaintext for dev)
    try:
        execute_query(
            "UPDATE users SET password = %s WHERE user_id = %s",
            (new_password, user_id),
            fetch=False,
        )
        flash('Password updated successfully.', 'success')
    except MySQLError as e:
        flash(f'Error updating password: {str(e)}', 'danger')

    return redirect(url_for('faculty.profile'))


# ── API endpoints (JSON) ────────────────────────────────────

@faculty_bp.route('/api/course-students/<int:course_id>')
@login_required
@role_required('faculty')
def api_course_students(course_id):
    """Returns JSON list of students for dynamic course switching."""
    fid = session['entity_id']
    if not _owns_course(fid, course_id):
        return jsonify({'error': 'Access denied'}), 403

    students = execute_query(
        """SELECT e.enrollment_id, s.first_name, s.last_name
           FROM enrollments e
           JOIN students s ON e.student_id = s.student_id
           WHERE e.section_id = %s AND e.status = 'active'
           ORDER BY s.first_name, s.last_name""",
        (course_id,),
    )
    return jsonify(students)


# ── timetable ────────────────────────────────────────────────

@faculty_bp.route('/timetable')
@login_required
@role_required('faculty')
def timetable():
    fid = session['entity_id']
    slots = execute_query(
        """SELECT ts.day_of_week, ts.start_time, ts.end_time, ts.room,
                  c.course_code, c.course_name, cs.section_code,
                  sm.name AS semester_name
           FROM timetable_slots ts
           JOIN course_sections cs ON ts.section_id = cs.section_id
           JOIN courses c ON cs.course_id = c.course_id
           LEFT JOIN semesters sm ON cs.semester_id = sm.semester_id
           WHERE cs.faculty_id = %s
           ORDER BY FIELD(ts.day_of_week,'Mon','Tue','Wed','Thu','Fri'), ts.start_time""",
        (fid,)
    )
    semester_name = slots[0]['semester_name'] if slots else ''
    return render_template('faculty/timetable.html', slots=slots or [], semester_name=semester_name)
