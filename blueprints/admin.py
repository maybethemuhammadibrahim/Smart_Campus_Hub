from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from db_connector import execute_query
from decorators import login_required, role_required

admin_bp = Blueprint('admin', __name__)


def _redirect_back(fallback_endpoint):
	referrer = request.referrer
	if referrer:
		return redirect(referrer)
	return redirect(url_for(fallback_endpoint))


@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
	total_students = execute_query("SELECT COUNT(*) AS total FROM students")
	total_faculty = execute_query("SELECT COUNT(*) AS total FROM faculty")
	total_courses = execute_query("SELECT COUNT(*) AS total FROM courses")
	total_enrollments = execute_query("SELECT COUNT(*) AS total FROM enrollments WHERE status='active'")

	recent_activity = execute_query(
		"""SELECT DATE_FORMAT(e.enrolled_at, '%%Y-%%m-%%d') AS date,
				  'Enrollment' AS type,
				  CONCAT(s.first_name, ' ', s.last_name, ' enrolled in ', c.course_code) AS details
		   FROM enrollments e
		   JOIN students s ON e.student_id = s.student_id
		   JOIN courses c ON e.course_id = c.course_id
		   ORDER BY e.enrolled_at DESC
		   LIMIT 10"""
	)

	return render_template(
		'admin/dashboard.html',
		total_students=total_students[0]['total'] if total_students else 0,
		total_faculty=total_faculty[0]['total'] if total_faculty else 0,
		total_courses=total_courses[0]['total'] if total_courses else 0,
		total_enrollments=total_enrollments[0]['total'] if total_enrollments else 0,
		recent_activity=recent_activity,
	)


@admin_bp.route('/students')
@login_required
@role_required('admin')
def students():
	records = execute_query(
		"""SELECT s.student_id, s.first_name, s.last_name, s.email,
				  s.program, s.batch_year, s.cgpa,
				  u.is_active
		   FROM students s
		   JOIN users u ON s.user_id = u.user_id
		   ORDER BY s.student_id DESC"""
	)
	return render_template('admin/students.html', students=records)


@admin_bp.route('/faculty')
@login_required
@role_required('admin')
def faculty_list():
	records = execute_query(
		"""SELECT f.faculty_id, f.first_name, f.last_name, f.email,
				  f.department, f.designation,
				  u.is_active
		   FROM faculty f
		   JOIN users u ON f.user_id = u.user_id
		   ORDER BY f.faculty_id DESC"""
	)
	return render_template('admin/faculty.html', faculty_list=records)


@admin_bp.route('/courses')
@login_required
@role_required('admin')
def courses():
	data = execute_query(
		"""SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
				  c.semester, c.max_capacity,
				  CONCAT(f.first_name, ' ', f.last_name) AS faculty_name,
				  COUNT(e.enrollment_id) AS enrolled_count
		   FROM courses c
		   LEFT JOIN faculty f ON c.faculty_id = f.faculty_id
		   LEFT JOIN enrollments e ON c.course_id = e.course_id AND e.status='active'
		   GROUP BY c.course_id, c.course_code, c.course_name, c.credit_hours,
					c.semester, c.max_capacity, f.first_name, f.last_name
		   ORDER BY c.course_code"""
	)
	return render_template('admin/courses.html', courses=data)


@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
	enrollment_report = execute_query(
		"""SELECT course_code, course_name, faculty_name,
				  enrolled_count AS enrolled,
				  max_capacity AS capacity,
				  fill_percentage
		   FROM v_admin_enrollment_report
		   ORDER BY enrolled_count DESC"""
	)

	gpa_dist = execute_query(
		"""SELECT
			   CASE
				   WHEN cgpa >= 3.5 THEN '3.5 - 4.0 (Dean''s List)'
				   WHEN cgpa >= 3.0 THEN '3.0 - 3.49 (Good)'
				   WHEN cgpa >= 2.5 THEN '2.5 - 2.99 (Satisfactory)'
				   WHEN cgpa >= 2.0 THEN '2.0 - 2.49 (Passing)'
				   ELSE                   'Below 2.0 (At Risk)'
			   END AS gpa_range,
			   COUNT(student_id) AS student_count
		   FROM students
		   GROUP BY gpa_range
		   ORDER BY MIN(cgpa) DESC"""
	)

	faculty_load = execute_query(
		"""SELECT
			   CONCAT(f.first_name, ' ', f.last_name) AS faculty_name,
			   f.department,
			   COUNT(DISTINCT c.course_id) AS course_count,
			   COALESCE(SUM(sub.enrolled), 0) AS total_students
		   FROM faculty f
		   LEFT JOIN courses c ON f.faculty_id = c.faculty_id
		   LEFT JOIN (
			   SELECT course_id, COUNT(*) AS enrolled
			   FROM enrollments
			   WHERE status = 'active'
			   GROUP BY course_id
		   ) sub ON c.course_id = sub.course_id
		   GROUP BY f.faculty_id, f.first_name, f.last_name, f.department
		   ORDER BY total_students DESC"""
	)

	return render_template(
		'admin/reports.html',
		enrollment_report=enrollment_report,
		gpa_dist=gpa_dist,
		faculty_load=faculty_load,
	)


@admin_bp.route('/students/add', methods=['POST'])
@login_required
@role_required('admin')
def add_student():
	first_name = request.form.get('first_name', '').strip()
	last_name = request.form.get('last_name', '').strip()
	email = request.form.get('email', '').strip()
	program = request.form.get('program', '').strip()
	batch_year = request.form.get('batch_year', '').strip()
	username = request.form.get('username', '').strip()
	password = request.form.get('password', '')

	if not all([first_name, last_name, email, program, batch_year, username, password]):
		flash('All student fields are required.', 'danger')
		return _redirect_back('admin.students')

	user_id = execute_query(
		"INSERT INTO users (username, password, role, is_active) VALUES (%s, %s, 'student', 1)",
		(username, generate_password_hash(password)),
		fetch=False,
	)

	execute_query(
		"""INSERT INTO students (user_id, first_name, last_name, email, program, batch_year)
		   VALUES (%s, %s, %s, %s, %s, %s)""",
		(user_id, first_name, last_name, email, program, batch_year),
		fetch=False,
	)

	flash('Student added successfully.', 'success')
	return _redirect_back('admin.students')


@admin_bp.route('/faculty/add', methods=['POST'])
@login_required
@role_required('admin')
def add_faculty():
	first_name = request.form.get('first_name', '').strip()
	last_name = request.form.get('last_name', '').strip()
	email = request.form.get('email', '').strip()
	department = request.form.get('department', '').strip()
	designation = request.form.get('designation', '').strip()
	username = request.form.get('username', '').strip()
	password = request.form.get('password', '')

	if not all([first_name, last_name, email, department, designation, username, password]):
		flash('All faculty fields are required.', 'danger')
		return _redirect_back('admin.faculty_list')

	user_id = execute_query(
		"INSERT INTO users (username, password, role, is_active) VALUES (%s, %s, 'faculty', 1)",
		(username, generate_password_hash(password)),
		fetch=False,
	)

	execute_query(
		"""INSERT INTO faculty (user_id, first_name, last_name, email, department, designation)
		   VALUES (%s, %s, %s, %s, %s, %s)""",
		(user_id, first_name, last_name, email, department, designation),
		fetch=False,
	)

	flash('Faculty added successfully.', 'success')
	return _redirect_back('admin.faculty_list')


@admin_bp.route('/courses/create', methods=['POST'])
@login_required
@role_required('admin')
def create_course():
	course_code = request.form.get('course_code', '').strip()
	course_name = request.form.get('course_name', '').strip()
	credit_hours = request.form.get('credit_hours', '').strip()
	semester = request.form.get('semester', '').strip()
	max_capacity = request.form.get('max_capacity', '').strip()

	if not all([course_code, course_name, credit_hours, semester, max_capacity]):
		flash('All course fields are required.', 'danger')
		return _redirect_back('admin.courses')

	execute_query(
		"""INSERT INTO courses (course_code, course_name, credit_hours, semester, max_capacity)
		   VALUES (%s, %s, %s, %s, %s)""",
		(course_code, course_name, credit_hours, semester, max_capacity),
		fetch=False,
	)

	flash('Course created successfully.', 'success')
	return _redirect_back('admin.courses')


@admin_bp.route('/students/<int:student_id>/edit')
@login_required
@role_required('admin')
def edit_student(student_id):
	flash(f'Edit student #{student_id} is not implemented yet.', 'info')
	return redirect(url_for('admin.students'))


@admin_bp.route('/faculty/<int:faculty_id>/edit')
@login_required
@role_required('admin')
def edit_faculty(faculty_id):
	flash(f'Edit faculty #{faculty_id} is not implemented yet.', 'info')
	return redirect(url_for('admin.faculty_list'))
