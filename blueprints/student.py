from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from db_connector import execute_query, call_procedure
from decorators import login_required, role_required

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    sid = session['entity_id']
    student = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))

    # Fixed: JOIN through course_sections to reach courses + faculty
    enrolled = execute_query(
        """SELECT c.course_name, c.course_code, c.credit_hours,
                  cs.section_code, sm.name AS semester_name,
                  CONCAT(f.first_name, ' ', f.last_name) AS faculty_name
           FROM enrollments e
           JOIN course_sections cs ON e.section_id = cs.section_id
           JOIN courses c ON cs.course_id = c.course_id
           LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
           LEFT JOIN semesters sm ON cs.semester_id = sm.semester_id
           WHERE e.student_id = %s AND e.status = 'active'
           ORDER BY c.course_code""",
        (sid,),
    )

    # Fixed: cgpa from v_student_cgpa view
    cgpa_row = execute_query(
        "SELECT cgpa FROM v_student_cgpa WHERE student_id=%s",
        (sid,),
    )
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else 0.00

    return render_template('student/dashboard.html',
                           student=student[0], enrolled=enrolled, cgpa=cgpa)

@student_bp.route('/courses')
@login_required
@role_required('student')
def available_courses():
    sid = session['entity_id']

    # ── UI-layer Rule 1 filter ──────────────────────────────────────────────
    # Hide ALL sections of any course the student is already actively enrolled
    # in during the same semester — not just the exact section they're in.
    # This prevents the UI from offering CS-101-B when the student is already
    # in CS-101-A.  The DB trigger (trg_enrollment_no_duplicate_course_in_semester)
    # is the authoritative guard; this is a UX improvement on top of it.
    # ────────────────────────────────────────────────────────────────────────
    courses = execute_query(
        """SELECT cs.section_id, c.course_code, c.course_name, c.credit_hours,
                  cs.section_code, sm.name AS semester_name,
                  CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
                  cs.max_capacity - COUNT(e.enrollment_id) AS seats_left
           FROM course_sections cs
           JOIN courses c ON cs.course_id = c.course_id
           JOIN semesters sm ON cs.semester_id = sm.semester_id AND sm.is_active = TRUE
           LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
           LEFT JOIN enrollments e ON cs.section_id = e.section_id AND e.status='active'
           WHERE
               -- Rule 1: exclude sections of courses already taken this semester
               cs.course_id NOT IN (
                   SELECT cs2.course_id
                   FROM enrollments e2
                   JOIN course_sections cs2 ON e2.section_id = cs2.section_id
                   WHERE e2.student_id = %s
                     AND e2.status = 'active'
                     AND cs2.semester_id = sm.semester_id
               )
           GROUP BY cs.section_id, c.course_code, c.course_name, c.credit_hours,
                    cs.section_code, sm.name, f.first_name, f.last_name, cs.max_capacity
           HAVING seats_left > 0""",
        (sid,)
    )
    return render_template('student/courses.html', courses=courses)

@student_bp.route('/enroll/<int:section_id>', methods=['POST'])
@login_required
@role_required('student')
def enroll(section_id):
    sid = session['entity_id']

    # ── Python pre-flight checks (application layer) ─────────────────────────
    # These run BEFORE the stored procedure call so the user sees a clean
    # flash message. The DB triggers (15 & 16) are the authoritative backstop
    # for any bypass path; these checks just improve UX responsiveness.

    # Rule 1: No enrollment in another section of the same course this semester
    conflict_row = execute_query(
        """SELECT COUNT(*) AS cnt
           FROM   enrollments e
           JOIN   course_sections cs  ON e.section_id  = cs.section_id
           JOIN   course_sections cs2 ON cs2.section_id = %s
           WHERE  e.student_id   = %s
             AND  e.status        = 'active'
             AND  cs.course_id    = cs2.course_id
             AND  cs.semester_id  = cs2.semester_id""",
        (section_id, sid)
    )
    if conflict_row and conflict_row[0]['cnt'] > 0:
        flash('You are already enrolled in another section of this course '
              'this semester.', 'warning')
        return redirect(url_for('student.available_courses'))

    # Rule 2: Max 6 active courses per semester
    overload_row = execute_query(
        """SELECT COUNT(*) AS cnt
           FROM   enrollments e
           JOIN   course_sections cs  ON e.section_id  = cs.section_id
           JOIN   course_sections cs2 ON cs2.section_id = %s
           WHERE  e.student_id   = %s
             AND  e.status        = 'active'
             AND  cs.semester_id  = cs2.semester_id""",
        (section_id, sid)
    )
    if overload_row and overload_row[0]['cnt'] >= 6:
        flash('You have reached the maximum of 6 active courses '
              'for this semester.', 'warning')
        return redirect(url_for('student.available_courses'))
    # ─────────────────────────────────────────────────────────────────────────

    try:
        # Use stored procedure — handles capacity, duplicates, both rules,
        # and grade row creation inside a single atomic transaction.
        result = call_procedure(
            'RegisterStudentInCourse', (sid, section_id, '', 0)
        )
        # OUT params: result[2] = p_message, result[3] = p_success
        sp_message = str(result[2]) if result[2] is not None else 'Enrollment processed.'
        sp_success = int(result[3]) if result[3] is not None else 0

        if sp_success:
            flash(sp_message, 'success')
        else:
            flash(sp_message, 'warning')
    except Exception as e:
        flash(f"Error enrolling: {e}", "danger")

    return redirect(url_for('student.available_courses'))

@student_bp.route('/attendance')
@login_required
@role_required('student')
def attendance():
    sid = session['entity_id']
    selected_semester = request.args.get('semester', '').strip()

    # Distinct semesters this student has attendance records in
    semesters = execute_query(
        "SELECT DISTINCT semester_name, semester_start FROM v_attendance_summary WHERE student_id=%s ORDER BY semester_start",
        (sid,),
    )
    semester_list = [r['semester_name'] for r in semesters if r.get('semester_name')]

    # Fetch attendance — filtered if semester selected, full otherwise
    if selected_semester:
        data = execute_query(
            "SELECT * FROM v_attendance_summary WHERE student_id=%s AND semester_name=%s",
            (sid, selected_semester),
        )
    else:
        data = execute_query(
            "SELECT * FROM v_attendance_summary WHERE student_id=%s",
            (sid,),
        )

    return render_template(
        'student/attendance.html',
        records=data,
        semesters=semester_list,
        selected_semester=selected_semester,
    )

@student_bp.route('/grades')
@login_required
@role_required('student')
def grades():
    sid = session['entity_id']
    selected_semester = request.args.get('semester', '').strip()

    # Distinct semesters this student has transcript/grade records in
    semesters = execute_query(
        "SELECT DISTINCT semester_name, semester_start FROM v_student_transcript WHERE student_id=%s ORDER BY semester_start",
        (sid,),
    )
    semester_list = [r['semester_name'] for r in semesters if r.get('semester_name')]

    # Fetch grades — filtered if semester selected, full otherwise
    if selected_semester:
        data = execute_query(
            "SELECT * FROM v_student_transcript WHERE student_id=%s AND semester_name=%s",
            (sid, selected_semester),
        )
    else:
        data = execute_query(
            "SELECT * FROM v_student_transcript WHERE student_id=%s",
            (sid,),
        )

    # CGPA is always cumulative (not filtered by semester)
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else 0.00

    return render_template(
        'student/grades.html',
        grades=data,
        cgpa=cgpa,
        semesters=semester_list,
        selected_semester=selected_semester,
    )

@student_bp.route('/transcript')
@login_required
@role_required('student')
def transcript():
    sid = session['entity_id']
    data = execute_query(
        "SELECT * FROM v_student_transcript WHERE student_id=%s ORDER BY semester_start, course_code",
        (sid,),
    )
    student = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))

    # Fixed: cgpa from v_student_cgpa view
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else 0.00

    # Group rows by semester_name (simple ordered dict)
    semester_order = []
    semester_buckets = {}
    for row in (data or []):
        sem = row.get('semester_name') or 'Unknown'
        if sem not in semester_buckets:
            semester_order.append(sem)
            semester_buckets[sem] = []
        semester_buckets[sem].append(row)

    # Build grouped list with per-semester summary
    grouped_transcript = []
    for sem in semester_order:
        rows = semester_buckets[sem]
        total_credits = 0
        gpa_credits = 0
        weighted_points = 0.0
        for r in rows:
            ch = r.get('credit_hours') or 0
            gp = r.get('grade_points')
            total_credits += ch
            if gp is not None:
                gpa_credits += ch
                weighted_points += float(gp) * ch
        sgpa = round(weighted_points / gpa_credits, 2) if gpa_credits > 0 else None
        grouped_transcript.append({
            'semester_name': sem,
            'rows': rows,
            'summary': {
                'total_credits': total_credits,
                'gpa_credits': gpa_credits,
                'sgpa': sgpa,
            },
        })

    return render_template(
        'student/transcript.html',
        grouped_transcript=grouped_transcript,
        student=student[0] if student else {},
        cgpa=cgpa,
    )

@student_bp.route('/profile')
@login_required
@role_required('student')
def profile():
    sid = session['entity_id']
    student = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else 0.00
    enrolled = execute_query(
        "SELECT COUNT(*) AS cnt FROM enrollments WHERE student_id=%s AND status='active'",
        (sid,),
    )
    enrolled_count = enrolled[0]['cnt'] if enrolled else 0
    return render_template('student/profile.html',
                           student=student[0] if student else {},
                           cgpa=cgpa, enrolled_count=enrolled_count)

@student_bp.route('/change-password', methods=['POST'])
@login_required
@role_required('student')
def change_password():
    user_id = session['user_id']

    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not all([current_password, new_password, confirm_password]):
        flash('All password fields are required.', 'danger')
        return redirect(url_for('student.profile'))

    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('student.profile'))

    if len(new_password) < 4:
        flash('Password must be at least 4 characters long.', 'danger')
        return redirect(url_for('student.profile'))

    user = execute_query("SELECT password FROM users WHERE user_id=%s", (user_id,))
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('student.profile'))

    # Verify current password (support both hashed and plaintext — same as auth.py)
    stored_pw = user[0]['password']
    password_ok = False
    try:
        password_ok = check_password_hash(stored_pw, current_password)
    except Exception:
        pass
    if not password_ok:
        password_ok = (stored_pw == current_password)

    if not password_ok:
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('student.profile'))

    # Store new password (plaintext for dev)
    execute_query(
        "UPDATE users SET password = %s WHERE user_id = %s",
        (new_password, user_id),
        fetch=False,
    )
    flash('Password updated successfully.', 'success')
    return redirect(url_for('student.profile'))


@student_bp.route('/timetable')
@login_required
@role_required('student')
def timetable():
    sid = session['entity_id']
    slots = execute_query(
        """SELECT ts.day_of_week, ts.start_time, ts.end_time, ts.room,
                  c.course_code, c.course_name, cs.section_code,
                  CONCAT(f.first_name, ' ', f.last_name) AS faculty_name,
                  sm.name AS semester_name
           FROM timetable_slots ts
           JOIN course_sections cs ON ts.section_id = cs.section_id
           JOIN courses c ON cs.course_id = c.course_id
           LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
           LEFT JOIN semesters sm ON cs.semester_id = sm.semester_id
           WHERE ts.section_id IN (
               SELECT e.section_id FROM enrollments e
               WHERE e.student_id = %s AND e.status = 'active'
           )
           ORDER BY FIELD(ts.day_of_week,'Mon','Tue','Wed','Thu','Fri'), ts.start_time""",
        (sid,)
    )
    # Get semester name for display
    semester_name = slots[0]['semester_name'] if slots else ''
    return render_template('student/timetable.html', slots=slots or [], semester_name=semester_name)