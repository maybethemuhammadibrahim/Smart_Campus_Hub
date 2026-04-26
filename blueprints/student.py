from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from db_connector import execute_query
from decorators import login_required, role_required
import mysql.connector
from config import Config

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

    # Fixed: use course_sections for seats, faculty, and section info
    courses = execute_query(
        """SELECT cs.section_id, c.course_code, c.course_name, c.credit_hours,
                  cs.section_code, sm.name AS semester_name,
                  CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
                  cs.max_capacity - COUNT(e.enrollment_id) AS seats_left
           FROM course_sections cs
           JOIN courses c ON cs.course_id = c.course_id
           JOIN semesters sm ON cs.semester_id = sm.semester_id
           LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
           LEFT JOIN enrollments e ON cs.section_id = e.section_id AND e.status='active'
           WHERE cs.section_id NOT IN (
               SELECT section_id FROM enrollments
               WHERE student_id=%s AND status='active'
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
    # Call stored procedure via direct connection (OUT params)
    # SP now expects section_id (p_section_id)
    conn   = mysql.connector.connect(
        host=Config.DB_HOST, user=Config.DB_USER,
        password=Config.DB_PASS, database=Config.DB_NAME
    )
    cursor = conn.cursor()
    args   = (sid, section_id, '', 0)
    cursor.callproc('RegisterStudentInCourse', args)
    conn.commit()
    # Fetch OUT params
    for r in cursor.stored_results():
        pass
    # Re-query OUT values
    cursor.execute("SELECT @_RegisterStudentInCourse_2, @_RegisterStudentInCourse_3")
    row = cursor.fetchone()
    message, success = row
    cursor.close()
    conn.close()
    flash(message, "success" if success else "danger")
    return redirect(url_for('student.available_courses'))

@student_bp.route('/attendance')
@login_required
@role_required('student')
def attendance():
    sid = session['entity_id']
    selected_semester = request.args.get('semester', '').strip()

    # Distinct semesters this student has attendance records in
    semesters = execute_query(
        "SELECT DISTINCT semester_name FROM v_attendance_summary WHERE student_id=%s ORDER BY semester_name",
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
    data = execute_query("SELECT * FROM v_student_transcript WHERE student_id=%s", (sid,))
    # Fixed: cgpa from v_student_cgpa view (no longer a stored column)
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else 0.00
    return render_template('student/grades.html', grades=data, cgpa=cgpa)

@student_bp.route('/transcript')
@login_required
@role_required('student')
def transcript():
    sid = session['entity_id']
    data = execute_query("SELECT * FROM v_student_transcript WHERE student_id=%s ORDER BY enrolled_at", (sid,))
    student = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))
    # Fixed: cgpa from v_student_cgpa view
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else 0.00
    return render_template('student/transcript.html',
                           transcript=data, student=student[0], cgpa=cgpa)

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

    if not check_password_hash(user[0]['password'], current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('student.profile'))

    # Store hashed password
    hashed = generate_password_hash(new_password)
    execute_query(
        "UPDATE users SET password = %s WHERE user_id = %s",
        (hashed, user_id),
        fetch=False,
    )
    flash('Password updated successfully.', 'success')
    return redirect(url_for('student.profile'))