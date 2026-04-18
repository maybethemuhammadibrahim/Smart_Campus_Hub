from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from db_connector import execute_query
from decorators import login_required, role_required

faculty_bp = Blueprint('faculty', __name__)


def _faculty_courses(faculty_id):
	return execute_query(
		"""SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
				  COUNT(e.enrollment_id) AS enrolled_count
		   FROM courses c
		   LEFT JOIN enrollments e ON c.course_id = e.course_id AND e.status = 'active'
		   WHERE c.faculty_id = %s
		   GROUP BY c.course_id, c.course_code, c.course_name, c.credit_hours
		   ORDER BY c.course_code""",
		(faculty_id,),
	)


def _owns_course(faculty_id, course_id):
	row = execute_query(
		"SELECT course_id FROM courses WHERE course_id=%s AND faculty_id=%s",
		(course_id, faculty_id),
	)
	return bool(row)


@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty')
def dashboard():
	fid = session['entity_id']
	faculty = execute_query("SELECT * FROM faculty WHERE faculty_id=%s", (fid,))
	courses = _faculty_courses(fid)
	total_students = sum((course.get('enrolled_count') or 0) for course in courses)

	return render_template(
		'faculty/dashboard.html',
		faculty=faculty[0] if faculty else {},
		courses=courses,
		total_students=total_students,
	)


@faculty_bp.route('/my-courses')
@login_required
@role_required('faculty')
def my_courses():
	fid = session['entity_id']
	courses = _faculty_courses(fid)
	return render_template('faculty/my_courses.html', courses=courses)


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
		return render_template('faculty/roster.html', students=[], course_name='No Course Selected')

	if not _owns_course(fid, course_id):
		flash('You do not have access to this course roster.', 'danger')
		return redirect(url_for('faculty.my_courses'))

	students = execute_query(
		"""SELECT s.student_id, s.first_name, s.last_name, s.email,
				  e.enrollment_id, e.enrolled_at,
				  att.attendance_percentage,
				  g.letter_grade
		   FROM enrollments e
		   JOIN students s ON e.student_id = s.student_id
		   LEFT JOIN v_attendance_summary att ON att.enrollment_id = e.enrollment_id
		   LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
		   WHERE e.course_id = %s AND e.status = 'active'
		   ORDER BY s.first_name, s.last_name""",
		(course_id,),
	)
	course = execute_query("SELECT course_name FROM courses WHERE course_id=%s", (course_id,))

	return render_template(
		'faculty/roster.html',
		students=students,
		course_name=course[0]['course_name'] if course else 'Course',
	)


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
			   WHERE e.course_id=%s AND e.status='active'
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
	except ValueError:
		flash('Please select a valid course.', 'danger')
		return redirect(url_for('faculty.mark_attendance'))

	attendance_date = request.form.get('attendance_date')
	if not attendance_date:
		flash('Attendance date is required.', 'danger')
		return redirect(url_for('faculty.mark_attendance', course_id=course_id))

	if not _owns_course(fid, course_id):
		flash('You do not have access to submit attendance for this course.', 'danger')
		return redirect(url_for('faculty.my_courses'))

	enrollments = execute_query(
		"SELECT enrollment_id FROM enrollments WHERE course_id=%s AND status='active'",
		(course_id,),
	)

	if not enrollments:
		flash('No active students found for the selected course.', 'warning')
		return redirect(url_for('faculty.mark_attendance', course_id=course_id))

	for row in enrollments:
		enrollment_id = row['enrollment_id']
		status = request.form.get(f'status_{enrollment_id}', 'present')
		if status not in ('present', 'absent', 'late'):
			status = 'present'

		execute_query(
			"""INSERT INTO attendance (enrollment_id, class_date, status, marked_by)
			   VALUES (%s, %s, %s, %s)
			   ON DUPLICATE KEY UPDATE
				 status = VALUES(status),
				 marked_by = VALUES(marked_by)""",
			(enrollment_id, attendance_date, status, marker_user_id),
			fetch=False,
		)

	flash('Attendance submitted successfully.', 'success')
	return redirect(url_for('faculty.mark_attendance', course_id=course_id))


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
					  g.marks_obtained AS marks, g.letter_grade
			   FROM enrollments e
			   JOIN students s ON e.student_id = s.student_id
			   LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
			   WHERE e.course_id = %s AND e.status = 'active'
			   ORDER BY s.first_name, s.last_name""",
			(course_id,),
		)
		course = execute_query("SELECT course_name FROM courses WHERE course_id=%s", (course_id,))
		if course:
			course_name = course[0]['course_name']

	return render_template(
		'faculty/enter_grades.html',
		students=students,
		course_id=course_id,
		course_name=course_name,
		courses=courses,
	)


@faculty_bp.route('/grades/save', methods=['POST'])
@login_required
@role_required('faculty')
def save_grades():
	fid = session['entity_id']

	try:
		course_id = int(request.form.get('course_id', '0'))
	except ValueError:
		flash('Invalid course selected.', 'danger')
		return redirect(url_for('faculty.enter_grades'))

	if not _owns_course(fid, course_id):
		flash('You do not have access to save grades for this course.', 'danger')
		return redirect(url_for('faculty.my_courses'))

	enrollments = execute_query(
		"SELECT enrollment_id FROM enrollments WHERE course_id=%s AND status='active'",
		(course_id,),
	)

	updated = 0
	for row in enrollments:
		enrollment_id = row['enrollment_id']
		marks_raw = request.form.get(f'marks_{enrollment_id}')
		if marks_raw in (None, ''):
			continue

		try:
			marks = float(marks_raw)
		except ValueError:
			continue

		marks = max(0.0, min(100.0, marks))

		execute_query(
			"""INSERT INTO grades (
					enrollment_id, marks_obtained, total_marks, letter_grade, grade_points
				)
				VALUES (
					%s, %s, 100,
					CASE
						WHEN %s >= 90 THEN 'A'
						WHEN %s >= 85 THEN 'A-'
						WHEN %s >= 80 THEN 'B+'
						WHEN %s >= 75 THEN 'B'
						WHEN %s >= 70 THEN 'B-'
						WHEN %s >= 65 THEN 'C+'
						WHEN %s >= 60 THEN 'C'
						ELSE 'F'
					END,
					CASE
						WHEN %s >= 90 THEN 4.00
						WHEN %s >= 85 THEN 3.70
						WHEN %s >= 80 THEN 3.30
						WHEN %s >= 75 THEN 3.00
						WHEN %s >= 70 THEN 2.70
						WHEN %s >= 65 THEN 2.30
						WHEN %s >= 60 THEN 2.00
						ELSE 0.00
					END
				)
				ON DUPLICATE KEY UPDATE
					marks_obtained = VALUES(marks_obtained),
					total_marks = VALUES(total_marks),
					letter_grade = VALUES(letter_grade),
					grade_points = VALUES(grade_points)""",
			(
				enrollment_id,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
				marks,
			),
			fetch=False,
		)
		updated += 1

	execute_query(
		"""UPDATE students s
		   SET s.cgpa = COALESCE((
			   SELECT ROUND(SUM(g.grade_points * c.credit_hours) / NULLIF(SUM(c.credit_hours), 0), 2)
			   FROM enrollments e
			   JOIN courses c ON e.course_id = c.course_id
			   JOIN grades g ON e.enrollment_id = g.enrollment_id
			   WHERE e.student_id = s.student_id
				 AND e.status = 'active'
				 AND g.grade_points IS NOT NULL
		   ), 0.00)
		   WHERE s.student_id IN (
			   SELECT DISTINCT e2.student_id
			   FROM enrollments e2
			   WHERE e2.course_id = %s AND e2.status = 'active'
		   )""",
		(course_id,),
		fetch=False,
	)

	flash(f'Grades saved for {updated} student(s).', 'success')
	return redirect(url_for('faculty.enter_grades', course_id=course_id))
