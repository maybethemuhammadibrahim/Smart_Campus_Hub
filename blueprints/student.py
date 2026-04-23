from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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
    # Fetch computed CGPA from view (students.cgpa column no longer exists)
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else '0.00'
    enrolled = execute_query(
        """SELECT c.course_name, c.course_code, c.credit_hours,
                  CONCAT(f.first_name, ' ', f.last_name) AS faculty_name
           FROM enrollments e
           JOIN course_sections cs ON e.section_id = cs.section_id
           JOIN courses c ON cs.course_id = c.course_id
           LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
           WHERE e.student_id = %s AND e.status = 'active'
           ORDER BY c.course_code""",
        (sid,),
    )
    return render_template('student/dashboard.html',
                           student=student[0], enrolled=enrolled, cgpa=cgpa)

@student_bp.route('/courses')
@login_required
@role_required('student')
def available_courses():
    sid = session['entity_id']
    courses = execute_query(
        """SELECT cs.section_id AS course_id,
                  c.course_code, c.course_name, c.credit_hours,
                  CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
                  sm.name AS semester_name,
                  cs.max_capacity - COUNT(e.enrollment_id) AS seats_left
           FROM course_sections cs
           JOIN courses c ON cs.course_id = c.course_id
           LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
           LEFT JOIN semesters sm ON cs.semester_id = sm.semester_id
           LEFT JOIN enrollments e ON cs.section_id = e.section_id AND e.status = 'active'
           WHERE cs.section_id NOT IN (
               SELECT section_id FROM enrollments
               WHERE student_id=%s AND status='active'
           )
           GROUP BY cs.section_id, c.course_code, c.course_name, c.credit_hours,
                    f.first_name, f.last_name, sm.name, cs.max_capacity
           HAVING seats_left > 0""",
        (sid,)
    )
    return render_template('student/courses.html', courses=courses)

@student_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
@role_required('student')
def enroll(course_id):
    # course_id in the URL now carries section_id (courses page passes cs.section_id)
    sid        = session['entity_id']
    section_id = course_id          # URL param re-used; SP now expects section_id
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
    data = execute_query("SELECT * FROM v_attendance_summary WHERE student_id=%s", (sid,))
    return render_template('student/attendance.html', records=data)

@student_bp.route('/grades')
@login_required
@role_required('student')
def grades():
    sid = session['entity_id']
    data = execute_query("SELECT * FROM v_student_transcript WHERE student_id=%s", (sid,))
    # Fetch computed CGPA from view (students.cgpa column no longer exists)
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else '0.00'
    return render_template('student/grades.html', grades=data, cgpa=cgpa)

@student_bp.route('/transcript')
@login_required
@role_required('student')
def transcript():
    sid = session['entity_id']
    data = execute_query(
        "SELECT * FROM v_student_transcript WHERE student_id=%s ORDER BY enrolled_at",
        (sid,)
    )
    student  = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))
    cgpa_row = execute_query("SELECT cgpa FROM v_student_cgpa WHERE student_id=%s", (sid,))
    cgpa = cgpa_row[0]['cgpa'] if cgpa_row else '0.00'
    return render_template('student/transcript.html',
                           transcript=data, student=student[0], cgpa=cgpa)