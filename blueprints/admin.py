from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
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

	# Fixed: JOIN through course_sections to reach courses
	recent_activity = execute_query(
		"""SELECT DATE_FORMAT(e.enrolled_at, '%Y-%m-%d') AS date,
				  'Enrollment' AS type,
				  CONCAT(s.first_name, ' ', s.last_name, ' enrolled in ', c.course_code) AS details
		   FROM enrollments e
		   JOIN students s ON e.student_id = s.student_id
		   JOIN course_sections cs ON e.section_id = cs.section_id
		   JOIN courses c ON cs.course_id = c.course_id
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
	# Fixed: cgpa sourced via v_student_cgpa LEFT JOIN
	records = execute_query(
		"""SELECT s.student_id, s.first_name, s.last_name, s.email,
				  s.program, s.batch_year,
				  COALESCE(v.cgpa, 0.00) AS cgpa,
				  u.is_active
		   FROM students s
		   JOIN users u ON s.user_id = u.user_id
		   LEFT JOIN v_student_cgpa v ON s.student_id = v.student_id
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

	# Grouped by course + semester — aggregates faculty names across sections
	data = execute_query(
		"""SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
		          sm.semester_id, sm.name AS semester_name,
		          GROUP_CONCAT(
		              DISTINCT CONCAT(f.first_name, ' ', f.last_name)
		              ORDER BY f.first_name SEPARATOR ', '
		          ) AS faculty_names,
		          COUNT(DISTINCT cs.section_id) AS section_count,
		          COALESCE(SUM(sub.enrolled), 0) AS enrolled_count,
		          SUM(cs.max_capacity) AS total_capacity
		   FROM courses c
		   JOIN course_sections cs ON c.course_id = cs.course_id
		   JOIN semesters sm ON cs.semester_id = sm.semester_id
		   LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
		   LEFT JOIN (
		       SELECT section_id, COUNT(*) AS enrolled
		       FROM enrollments WHERE status = 'active'
		       GROUP BY section_id
		   ) sub ON cs.section_id = sub.section_id
		   GROUP BY c.course_id, c.course_code, c.course_name, c.credit_hours,
		            sm.semester_id, sm.name
		   ORDER BY c.course_code, sm.name"""
	)

	# Faculty list for the assign/create modals
	faculty_list = execute_query(
		"""SELECT f.faculty_id,
		          CONCAT(f.first_name, ' ', f.last_name) AS full_name,
		          f.department
		   FROM faculty f
		   JOIN users u ON f.user_id = u.user_id
		   WHERE u.is_active = 1
		   ORDER BY f.first_name"""
	)

	# Semesters for the create modal dropdown
	semesters = execute_query(
		"SELECT semester_id, name FROM semesters ORDER BY start_date DESC"
	)

	return render_template(
		'admin/courses.html',
		courses=data,
		faculty_list=faculty_list or [],
		semesters=semesters or [],

	)


@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
	enrollment_report = execute_query(
		"""SELECT course_code, course_name, section_code, semester_name,
				  faculty_name,
				  enrolled_count AS enrolled,
				  max_capacity AS capacity,
				  fill_percentage
		   FROM v_admin_enrollment_report
		   ORDER BY enrolled_count DESC"""
	)

	# Fixed: use v_student_cgpa instead of students.cgpa
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
		   FROM v_student_cgpa
		   GROUP BY gpa_range
		   ORDER BY MIN(cgpa) DESC"""
	)

	# Fixed: use course_sections instead of courses.faculty_id
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


@admin_bp.route('/semesters')
@login_required
@role_required('admin')
def semesters():
	records = execute_query(
		"""SELECT sm.*,
		          COUNT(DISTINCT cs.section_id)    AS section_count,
		          COUNT(DISTINCT e.enrollment_id)  AS enrollment_count,
		          COUNT(DISTINCT cs.faculty_id)     AS faculty_count,
		          COUNT(DISTINCT cs.course_id)      AS course_count
		   FROM semesters sm
		   LEFT JOIN course_sections cs ON sm.semester_id = cs.semester_id
		   LEFT JOIN enrollments e ON cs.section_id = e.section_id
		       AND e.status = 'active'
		   GROUP BY sm.semester_id
		   ORDER BY sm.start_date DESC"""
	)

	totals = execute_query(
		"""SELECT COUNT(*) AS total_semesters,
		          SUM(is_active) AS active_count
		   FROM semesters"""
	)

	return render_template(
		'admin/semesters.html',
		semesters=records,
		total_semesters=totals[0]['total_semesters'] if totals else 0,
		active_count=totals[0]['active_count']       if totals else 0,
	)


@admin_bp.route('/semesters/create', methods=['POST'])
@login_required
@role_required('admin')
def create_semester():
	name       = request.form.get('name', '').strip()
	start_date = request.form.get('start_date', '').strip()
	end_date   = request.form.get('end_date', '').strip()
	is_active  = request.form.get('is_active', '0')

	if not all([name, start_date, end_date]):
		flash('All semester fields are required.', 'danger')
		return _redirect_back('admin.semesters')

	try:
		execute_query(
			"""INSERT INTO semesters (name, start_date, end_date, is_active)
			   VALUES (%s, %s, %s, %s)""",
			(name, start_date, end_date, int(is_active)),
			fetch=False,
		)
		flash('Semester created successfully.', 'success')
	except Exception as e:
		err = str(e).lower()
		if 'duplicate' in err:
			flash('A semester with that name already exists.', 'danger')
		elif 'chk_semester_dates' in err:
			flash('End date must be after start date.', 'danger')
		else:
			flash(f'Error creating semester: {e}', 'danger')

	return _redirect_back('admin.semesters')


@admin_bp.route('/semesters/<int:semester_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_semester(semester_id):
	name       = request.form.get('name', '').strip()
	start_date = request.form.get('start_date', '').strip()
	end_date   = request.form.get('end_date', '').strip()
	is_active  = request.form.get('is_active', '0')

	if not all([name, start_date, end_date]):
		flash('All semester fields are required.', 'danger')
		return _redirect_back('admin.semesters')

	sem = execute_query(
		"SELECT semester_id FROM semesters WHERE semester_id = %s",
		(semester_id,)
	)
	if not sem:
		flash('Semester not found.', 'danger')
		return redirect(url_for('admin.semesters'))

	try:
		execute_query(
			"""UPDATE semesters
			   SET name = %s, start_date = %s, end_date = %s, is_active = %s
			   WHERE semester_id = %s""",
			(name, start_date, end_date, int(is_active), semester_id),
			fetch=False,
		)
		flash('Semester updated successfully.', 'success')
	except Exception as e:
		err = str(e).lower()
		if 'duplicate' in err:
			flash('A semester with that name already exists.', 'danger')
		elif 'chk_semester_dates' in err:
			flash('End date must be after start date.', 'danger')
		else:
			flash(f'Error updating semester: {e}', 'danger')

	return redirect(url_for('admin.semesters'))


@admin_bp.route('/semesters/<int:semester_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_semester(semester_id):
	sem = execute_query(
		"SELECT semester_id, name FROM semesters WHERE semester_id = %s",
		(semester_id,)
	)
	if not sem:
		flash('Semester not found.', 'danger')
		return redirect(url_for('admin.semesters'))

	execute_query(
		"DELETE FROM semesters WHERE semester_id = %s",
		(semester_id,),
		fetch=False,
	)
	flash(f'Semester "{sem[0]["name"]}" deleted successfully.', 'success')
	return redirect(url_for('admin.semesters'))


@admin_bp.route('/semesters/<int:semester_id>/stats')
@login_required
@role_required('admin')
def semester_stats(semester_id):
	# ── Semester info ──
	sem = execute_query(
		"SELECT * FROM semesters WHERE semester_id = %s",
		(semester_id,)
	)
	if not sem:
		flash('Semester not found.', 'danger')
		return redirect(url_for('admin.semesters'))
	semester = sem[0]

	# ── Overview stats (DB-side aggregation) ──
	overview = execute_query(
		"""SELECT COUNT(DISTINCT cs.section_id)   AS total_sections,
		          COUNT(DISTINCT e.enrollment_id)  AS total_enrollments,
		          COUNT(DISTINCT cs.course_id)      AS unique_courses,
		          COUNT(DISTINCT cs.faculty_id)     AS faculty_assigned
		   FROM course_sections cs
		   LEFT JOIN enrollments e ON cs.section_id = e.section_id
		       AND e.status = 'active'
		   WHERE cs.semester_id = %s""",
		(semester_id,)
	)
	stats = overview[0] if overview else {
		'total_sections': 0, 'total_enrollments': 0,
		'unique_courses': 0, 'faculty_assigned': 0
	}

	# ── Enrollment status breakdown (DB-side GROUP BY) ──
	enrollment_status = execute_query(
		"""SELECT e.status, COUNT(*) AS cnt
		   FROM enrollments e
		   JOIN course_sections cs ON e.section_id = cs.section_id
		   WHERE cs.semester_id = %s
		   GROUP BY e.status
		   ORDER BY FIELD(e.status, 'active', 'completed', 'dropped')""",
		(semester_id,)
	)

	# ── Course sections via existing view ──
	sections = execute_query(
		"""SELECT * FROM v_admin_enrollment_report
		   WHERE semester_name = %s
		   ORDER BY course_code, section_code""",
		(semester['name'],)
	)

	# ── Grade distribution (DB-side CASE WHEN + GROUP BY) ──
	grade_dist = execute_query(
		"""SELECT
		       CASE
		           WHEN g.grade_points >= 3.50 THEN 'A / A-'
		           WHEN g.grade_points >= 3.00 THEN 'B+ / B'
		           WHEN g.grade_points >= 2.50 THEN 'B- / C+'
		           WHEN g.grade_points >= 2.00 THEN 'C'
		           ELSE 'F'
		       END AS grade_range,
		       COUNT(*) AS student_count,
		       ROUND(AVG(g.marks_obtained), 1) AS avg_marks
		   FROM grades g
		   JOIN enrollments e  ON g.enrollment_id = e.enrollment_id
		   JOIN course_sections cs ON e.section_id = cs.section_id
		   WHERE cs.semester_id = %s
		     AND g.grade_points IS NOT NULL
		   GROUP BY grade_range
		   ORDER BY MIN(g.grade_points) DESC""",
		(semester_id,)
	)

	# ── Faculty workload (DB-side aggregation) ──
	faculty_load = execute_query(
		"""SELECT
		       CONCAT(f.first_name, ' ', f.last_name) AS faculty_name,
		       f.department,
		       COUNT(DISTINCT cs.section_id) AS section_count,
		       COALESCE(SUM(sub.enrolled), 0) AS total_students
		   FROM faculty f
		   JOIN course_sections cs ON f.faculty_id = cs.faculty_id
		       AND cs.semester_id = %s
		   LEFT JOIN (
		       SELECT section_id, COUNT(*) AS enrolled
		       FROM enrollments
		       WHERE status = 'active'
		       GROUP BY section_id
		   ) sub ON cs.section_id = sub.section_id
		   GROUP BY f.faculty_id, f.first_name, f.last_name, f.department
		   ORDER BY section_count DESC""",
		(semester_id,)
	)

	# ── Attendance overview per course (DB-side AVG) ──
	attendance_overview = execute_query(
		"""SELECT
		       c.course_code,
		       c.course_name,
		       cs.section_code,
		       COUNT(a.attendance_id) AS total_records,
		       SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS present_count,
		       ROUND(
		           SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)
		           / NULLIF(COUNT(a.attendance_id), 0) * 100, 1
		       ) AS attendance_pct
		   FROM course_sections cs
		   JOIN courses c ON cs.course_id = c.course_id
		   JOIN enrollments e ON cs.section_id = e.section_id
		   LEFT JOIN attendance a ON e.enrollment_id = a.enrollment_id
		   WHERE cs.semester_id = %s
		   GROUP BY c.course_id, c.course_code, c.course_name, cs.section_code
		   HAVING COUNT(a.attendance_id) > 0
		   ORDER BY attendance_pct DESC""",
		(semester_id,)
	)

	# ── Top performing students (DB-side weighted GPA) ──
	top_students = execute_query(
		"""SELECT
		       CONCAT(s.first_name, ' ', s.last_name) AS student_name,
		       s.program,
		       ROUND(
		           SUM(g.grade_points * c.credit_hours)
		           / NULLIF(SUM(c.credit_hours), 0), 2
		       ) AS semester_gpa,
		       COUNT(DISTINCT e.section_id) AS courses_taken
		   FROM students s
		   JOIN enrollments e ON s.student_id = e.student_id
		   JOIN course_sections cs ON e.section_id = cs.section_id
		   JOIN courses c ON cs.course_id = c.course_id
		   JOIN grades g ON e.enrollment_id = g.enrollment_id
		   WHERE cs.semester_id = %s
		     AND g.grade_points IS NOT NULL
		   GROUP BY s.student_id, s.first_name, s.last_name, s.program
		   ORDER BY semester_gpa DESC
		   LIMIT 5""",
		(semester_id,)
	)

	return render_template(
		'admin/semester_stats.html',
		semester=semester,
		stats=stats,
		enrollment_status=enrollment_status,
		sections=sections,
		grade_dist=grade_dist,
		faculty_load=faculty_load,
		attendance_overview=attendance_overview,
		top_students=top_students,
	)


@admin_bp.route('/students/add', methods=['POST'])
@login_required
@role_required('admin')
def add_student():
	first_name = request.form.get('first_name', '').strip()
	last_name = request.form.get('last_name', '').strip()
	email = request.form.get('email', '').strip()
	dob = request.form.get('dob', '').strip()
	program = request.form.get('program', '').strip()
	batch_year = request.form.get('batch_year', '').strip()
	username = request.form.get('username', '').strip()
	password = request.form.get('password', '')

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

	semester_id  = request.form.get('semester_id', '').strip()
	max_capacity = request.form.get('max_capacity', '').strip()
	faculty_id   = request.form.get('faculty_id', '').strip() or None


	if not all([course_code, course_name, credit_hours, semester_id, max_capacity]):
		flash('All course fields are required.', 'danger')
		return _redirect_back('admin.courses')


	# Validate semester exists
	sem = execute_query(
		"SELECT semester_id FROM semesters WHERE semester_id = %s",
		(semester_id,),
	)
	if not sem:
		flash('Selected semester not found.', 'danger')
		return _redirect_back('admin.courses')

	# Upsert catalog course (course_code must be unique)

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


	# Auto-generate section_code (A, B, C, ...)
	section_code = _next_section_code(course_id, int(semester_id))

	try:
		execute_query(
			"""INSERT INTO course_sections
			       (course_id, semester_id, faculty_id, section_code, max_capacity)
			   VALUES (%s, %s, %s, %s, %s)""",
			(course_id, semester_id, faculty_id, section_code, max_capacity),
			fetch=False,
		)
		flash('Course created successfully.', 'success')
	except Exception as e:
		err = str(e).lower()
		if 'duplicate' in err:
			flash('This course section already exists for the selected semester.', 'danger')
		else:
			flash(f'Error creating course: {e}', 'danger')

	return _redirect_back('admin.courses')


def _next_section_code(course_id, semester_id):
	"""Auto-generate the next section code (A, B, C, ...) for a course+semester."""
	existing = execute_query(
		"""SELECT section_code FROM course_sections
		   WHERE course_id = %s AND semester_id = %s
		   ORDER BY section_code DESC LIMIT 1""",
		(course_id, semester_id),
	)
	if not existing:
		return 'A'
	last = existing[0]['section_code']
	# Increment the last character: A→B, B→C, etc.
	return chr(ord(last[0]) + 1) if last and last[0].isalpha() else 'A'


@admin_bp.route('/courses/assign-faculty', methods=['POST'])
@login_required
@role_required('admin')
def assign_faculty():
	course_id    = request.form.get('course_id', '').strip()
	semester_id  = request.form.get('semester_id', '').strip()
	faculty_id   = request.form.get('faculty_id', '').strip()
	max_capacity = request.form.get('max_capacity', '40').strip()

	if not all([course_id, semester_id, faculty_id]):
		flash('Course, semester, and faculty are required.', 'danger')
		return _redirect_back('admin.courses')

	# Check if this faculty is already assigned to this course+semester
	already = execute_query(
		"""SELECT section_id FROM course_sections
		   WHERE course_id = %s AND semester_id = %s AND faculty_id = %s""",
		(course_id, semester_id, faculty_id),
	)
	if already:
		flash('This faculty member is already assigned to this course.', 'warning')
		return _redirect_back('admin.courses')

	# Check for an unassigned section first — fill it instead of creating a new one
	unassigned = execute_query(
		"""SELECT section_id FROM course_sections
		   WHERE course_id = %s AND semester_id = %s AND faculty_id IS NULL
		   LIMIT 1""",
		(course_id, semester_id),

	)

	try:
		if unassigned:
			execute_query(
				"UPDATE course_sections SET faculty_id = %s WHERE section_id = %s",
				(faculty_id, unassigned[0]['section_id']),
				fetch=False,
			)
		else:
			# Create a new section for the additional faculty assignment
			section_code = _next_section_code(int(course_id), int(semester_id))
			execute_query(
				"""INSERT INTO course_sections
				       (course_id, semester_id, faculty_id, section_code, max_capacity)
				   VALUES (%s, %s, %s, %s, %s)""",
				(course_id, semester_id, faculty_id, section_code, max_capacity),
				fetch=False,
			)
		flash('Faculty assigned successfully.', 'success')
	except Exception as e:
		flash(f'Error assigning faculty: {e}', 'danger')

	return _redirect_back('admin.courses')


@admin_bp.route('/courses/unassign-faculty', methods=['POST'])
@login_required
@role_required('admin')
def unassign_faculty():
	section_id = request.form.get('section_id', '').strip()

	if not section_id:
		flash('Section ID is required.', 'danger')
		return _redirect_back('admin.courses')

	section = execute_query(
		"SELECT section_id, faculty_id FROM course_sections WHERE section_id = %s",
		(section_id,)
	)
	if not section:
		flash('Section not found.', 'danger')
		return redirect(url_for('admin.courses'))

	execute_query(
		"UPDATE course_sections SET faculty_id = NULL WHERE section_id = %s",
		(section_id,),
		fetch=False,
	)
	flash('Faculty unassigned successfully.', 'success')
	return _redirect_back('admin.courses')


@admin_bp.route('/courses/<int:course_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_course(course_id):
	course_name  = request.form.get('course_name', '').strip()
	credit_hours = request.form.get('credit_hours', '').strip()

	if not all([course_name, credit_hours]):
		flash('Course name and credit hours are required.', 'danger')
		return _redirect_back('admin.courses')

	course = execute_query(
		"SELECT course_id FROM courses WHERE course_id = %s",
		(course_id,)
	)
	if not course:
		flash('Course not found.', 'danger')
		return redirect(url_for('admin.courses'))

	execute_query(
		"""UPDATE courses SET course_name = %s, credit_hours = %s
		   WHERE course_id = %s""",
		(course_name, credit_hours, course_id),
		fetch=False,
	)
	flash('Course updated successfully.', 'success')
	return redirect(url_for('admin.courses'))


@admin_bp.route('/courses/<int:course_id>/sections')
@login_required
@role_required('admin')
def course_sections_api(course_id):
	"""JSON endpoint returning faculty assignments for a course (used by Edit modal)."""
	semester_id = request.args.get('semester_id', '')
	if not semester_id:
		return jsonify([])

	sections = execute_query(
		"""SELECT cs.section_id, cs.section_code, cs.max_capacity,
		          cs.faculty_id,
		          CONCAT(f.first_name, ' ', f.last_name) AS faculty_name,
		          f.department
		   FROM course_sections cs
		   LEFT JOIN faculty f ON cs.faculty_id = f.faculty_id
		   WHERE cs.course_id = %s AND cs.semester_id = %s
		   ORDER BY cs.section_code""",
		(course_id, semester_id),
	)
	return jsonify(sections or [])


@admin_bp.route('/students/<int:student_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def update_student(student_id):
	first_name = request.form.get('first_name', '').strip()
	last_name = request.form.get('last_name', '').strip()
	email = request.form.get('email', '').strip()
	dob = request.form.get('dob', '').strip()
	program = request.form.get('program', '').strip()
	batch_year = request.form.get('batch_year', '').strip()
	is_active = request.form.get('is_active', '0')

	if not all([first_name, last_name, email, program, batch_year]):
		flash('All required fields must be filled.', 'danger')
		return _redirect_back('admin.students')

	# Get user_id for this student
	student = execute_query(
		"SELECT user_id FROM students WHERE student_id = %s",
		(student_id,)
	)

	if not student:
		flash('Student not found.', 'danger')
		return redirect(url_for('admin.students'))

	user_id = student[0]['user_id']

	# Update student info
	execute_query(
		"""UPDATE students 
		   SET first_name = %s, last_name = %s, email = %s, dob = %s, 
		       program = %s, batch_year = %s
		   WHERE student_id = %s""",
		(first_name, last_name, email, dob if dob else None, program, batch_year, student_id),
		fetch=False,
	)

	# Update user status
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
	first_name = request.form.get('first_name', '').strip()
	last_name = request.form.get('last_name', '').strip()
	email = request.form.get('email', '').strip()
	department = request.form.get('department', '').strip()
	designation = request.form.get('designation', '').strip()
	is_active = request.form.get('is_active', '0')

	if not all([first_name, last_name, email, department, designation]):
		flash('All required fields must be filled.', 'danger')
		return _redirect_back('admin.faculty_list')

	# Get user_id for this faculty
	faculty = execute_query(
		"SELECT user_id FROM faculty WHERE faculty_id = %s",
		(faculty_id,)
	)

	if not faculty:
		flash('Faculty not found.', 'danger')
		return redirect(url_for('admin.faculty_list'))

	user_id = faculty[0]['user_id']

	# Update faculty info
	execute_query(
		"""UPDATE faculty 
		   SET first_name = %s, last_name = %s, email = %s, 
		       department = %s, designation = %s
		   WHERE faculty_id = %s""",
		(first_name, last_name, email, department, designation, faculty_id),
		fetch=False,
	)

	# Update user status
	execute_query(
		"UPDATE users SET is_active = %s WHERE user_id = %s",
		(int(is_active), user_id),
		fetch=False,
	)

	flash('Faculty updated successfully.', 'success')
	return redirect(url_for('admin.faculty_list'))
