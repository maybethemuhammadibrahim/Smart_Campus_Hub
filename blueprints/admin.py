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
	total_students    = execute_query("SELECT COUNT(*) AS total FROM students")
	total_faculty     = execute_query("SELECT COUNT(*) AS total FROM faculty")
	total_courses     = execute_query("SELECT COUNT(*) AS total FROM courses")
	total_enrollments = execute_query("SELECT COUNT(*) AS total FROM enrollments WHERE status='active'")

	recent_activity = execute_query(
		"""SELECT DATE_FORMAT(e.enrolled_at, '%Y-%m-%d') AS date,
		          'Enrollment' AS type,
		          CONCAT(s.first_name, ' ', s.last_name, ' enrolled in ', c.course_code) AS details
		   FROM enrollments e
		   JOIN students        s  ON e.student_id  = s.student_id
		   JOIN course_sections cs ON e.section_id  = cs.section_id
		   JOIN courses         c  ON cs.course_id  = c.course_id
		   ORDER BY e.enrolled_at DESC
		   LIMIT 10"""
	)

	return render_template(
		'admin/dashboard.html',
		total_students=total_students[0]['total']       if total_students    else 0,
		total_faculty=total_faculty[0]['total']         if total_faculty     else 0,
		total_courses=total_courses[0]['total']         if total_courses     else 0,
		total_enrollments=total_enrollments[0]['total'] if total_enrollments else 0,
		recent_activity=recent_activity,
	)


@admin_bp.route('/students')
@login_required
@role_required('admin')
def students():
	records = execute_query(
		"""SELECT s.student_id, s.first_name, s.last_name, s.email,
		          s.program, s.batch_year, s.dob,
		          u.is_active,
		          vc.cgpa
		   FROM students s
		   JOIN users u ON s.user_id = u.user_id
		   LEFT JOIN v_student_cgpa vc ON vc.student_id = s.student_id
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
	# v_admin_enrollment_report already joins course_sections + courses + semesters + faculty
	data = execute_query(
		"""SELECT * FROM v_admin_enrollment_report ORDER BY course_code, semester_name"""
	)
	return render_template('admin/courses.html', courses=data)


@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
	enrollment_report = execute_query(
		"""SELECT course_code, course_name, faculty_name,
		          enrolled_count AS enrolled,
		          max_capacity   AS capacity,
		          fill_percentage
		   FROM v_admin_enrollment_report
		   ORDER BY enrolled_count DESC"""
	)

	# GPA distribution — uses v_student_cgpa (students.cgpa no longer exists)
	gpa_dist = execute_query(
		"""SELECT
		       CASE
		           WHEN vc.cgpa >= 3.5 THEN '3.5 - 4.0 (Dean''s List)'
		           WHEN vc.cgpa >= 3.0 THEN '3.0 - 3.49 (Good)'
		           WHEN vc.cgpa >= 2.5 THEN '2.5 - 2.99 (Satisfactory)'
		           WHEN vc.cgpa >= 2.0 THEN '2.0 - 2.49 (Passing)'
		           ELSE                     'Below 2.0 (At Risk)'
		       END AS gpa_range,
		       COUNT(vc.student_id) AS student_count
		   FROM v_student_cgpa vc
		   GROUP BY gpa_range
		   ORDER BY MIN(vc.cgpa) DESC"""
	)

	# Faculty load — uses course_sections (courses.faculty_id no longer exists)
	faculty_load = execute_query(
		"""SELECT
		       CONCAT(f.first_name, ' ', f.last_name) AS faculty_name,
		       f.department,
		       COUNT(DISTINCT cs.section_id) AS course_count,
		       COALESCE(SUM(sub.enrolled), 0) AS total_students
		   FROM faculty f
		   LEFT JOIN course_sections cs ON f.faculty_id = cs.faculty_id
		   LEFT JOIN (
		       SELECT section_id, COUNT(*) AS enrolled
		       FROM enrollments
		       WHERE status = 'active'
		       GROUP BY section_id
		   ) sub ON cs.section_id = sub.section_id
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
	first_name  = request.form.get('first_name', '').strip()
	last_name   = request.form.get('last_name', '').strip()
	email       = request.form.get('email', '').strip()
	dob         = request.form.get('dob', '').strip()
	program     = request.form.get('program', '').strip()
	batch_year  = request.form.get('batch_year', '').strip()
	username    = request.form.get('username', '').strip()
	password    = request.form.get('password', '')

	if not all([first_name, last_name, email, program, batch_year, username, password]):
		flash('All required student fields must be filled.', 'danger')
		return _redirect_back('admin.students')

	user_id = execute_query(
		"INSERT INTO users (username, password, role, is_active) VALUES (%s, %s, 'student', 1)",
		(username, generate_password_hash(password)),
		fetch=False,
	)

	execute_query(
		"""INSERT INTO students (user_id, first_name, last_name, email, dob, program, batch_year)
		   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
		(user_id, first_name, last_name, email, dob if dob else None, program, batch_year),
		fetch=False,
	)

	flash('Student added successfully.', 'success')
	return _redirect_back('admin.students')


@admin_bp.route('/faculty/add', methods=['POST'])
@login_required
@role_required('admin')
def add_faculty():
	first_name  = request.form.get('first_name', '').strip()
	last_name   = request.form.get('last_name', '').strip()
	email       = request.form.get('email', '').strip()
	department  = request.form.get('department', '').strip()
	designation = request.form.get('designation', '').strip()
	username    = request.form.get('username', '').strip()
	password    = request.form.get('password', '')

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
	course_code  = request.form.get('course_code', '').strip()
	course_name  = request.form.get('course_name', '').strip()
	credit_hours = request.form.get('credit_hours', '').strip()
	semester     = request.form.get('semester', '').strip()
	max_capacity = request.form.get('max_capacity', '').strip()
	section_code = request.form.get('section_code', 'A').strip() or 'A'

	if not all([course_code, course_name, credit_hours, semester, max_capacity]):
		flash('All course fields are required.', 'danger')
		return _redirect_back('admin.courses')

	# Step 1: resolve or create the semester row
	sem_rows = execute_query(
		"SELECT semester_id FROM semesters WHERE name = %s",
		(semester,),
	)
	if sem_rows:
		semester_id = sem_rows[0]['semester_id']
	else:
		# Create a placeholder semester (dates can be updated later)
		semester_id = execute_query(
			"""INSERT INTO semesters (name, start_date, end_date, is_active)
			   VALUES (%s, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 6 MONTH), FALSE)""",
			(semester,),
			fetch=False,
		)

	# Step 2: insert catalog course (course_code must be unique)
	existing = execute_query(
		"SELECT course_id FROM courses WHERE course_code = %s",
		(course_code,),
	)
	if existing:
		course_id = existing[0]['course_id']
	else:
		course_id = execute_query(
			"INSERT INTO courses (course_code, course_name, credit_hours) VALUES (%s, %s, %s)",
			(course_code, course_name, credit_hours),
			fetch=False,
		)

	# Step 3: insert the section offering
	execute_query(
		"""INSERT INTO course_sections
		       (course_id, semester_id, faculty_id, section_code, max_capacity)
		   VALUES (%s, %s, NULL, %s, %s)""",
		(course_id, semester_id, section_code, max_capacity),
		fetch=False,
	)

	flash('Course created successfully.', 'success')
	return _redirect_back('admin.courses')


@admin_bp.route('/students/<int:student_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_student(student_id):
	first_name  = request.form.get('first_name', '').strip()
	last_name   = request.form.get('last_name', '').strip()
	email       = request.form.get('email', '').strip()
	dob         = request.form.get('dob', '').strip()
	program     = request.form.get('program', '').strip()
	batch_year  = request.form.get('batch_year', '').strip()
	is_active   = request.form.get('is_active', '0')

	if not all([first_name, last_name, email, program, batch_year]):
		flash('All required fields must be filled.', 'danger')
		return _redirect_back('admin.students')

	student = execute_query(
		"SELECT user_id FROM students WHERE student_id = %s",
		(student_id,)
	)

	if not student:
		flash('Student not found.', 'danger')
		return redirect(url_for('admin.students'))

	user_id = student[0]['user_id']

	execute_query(
		"""UPDATE students
		   SET first_name = %s, last_name = %s, email = %s, dob = %s,
		       program = %s, batch_year = %s
		   WHERE student_id = %s""",
		(first_name, last_name, email, dob if dob else None, program, batch_year, student_id),
		fetch=False,
	)

	execute_query(
		"UPDATE users SET is_active = %s WHERE user_id = %s",
		(int(is_active), user_id),
		fetch=False,
	)

	flash('Student updated successfully.', 'success')
	return redirect(url_for('admin.students'))


@admin_bp.route('/faculty/<int:faculty_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_faculty(faculty_id):
	first_name  = request.form.get('first_name', '').strip()
	last_name   = request.form.get('last_name', '').strip()
	email       = request.form.get('email', '').strip()
	department  = request.form.get('department', '').strip()
	designation = request.form.get('designation', '').strip()
	is_active   = request.form.get('is_active', '0')

	if not all([first_name, last_name, email, department, designation]):
		flash('All required fields must be filled.', 'danger')
		return _redirect_back('admin.faculty_list')

	faculty = execute_query(
		"SELECT user_id FROM faculty WHERE faculty_id = %s",
		(faculty_id,)
	)

	if not faculty:
		flash('Faculty not found.', 'danger')
		return redirect(url_for('admin.faculty_list'))

	user_id = faculty[0]['user_id']

	execute_query(
		"""UPDATE faculty
		   SET first_name = %s, last_name = %s, email = %s,
		       department = %s, designation = %s
		   WHERE faculty_id = %s""",
		(first_name, last_name, email, department, designation, faculty_id),
		fetch=False,
	)

	execute_query(
		"UPDATE users SET is_active = %s WHERE user_id = %s",
		(int(is_active), user_id),
		fetch=False,
	)

	flash('Faculty updated successfully.', 'success')
	return redirect(url_for('admin.faculty_list'))
