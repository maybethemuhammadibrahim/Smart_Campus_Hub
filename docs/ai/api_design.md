# API Design

## Type
This is a server-rendered web application. There is no JSON REST API. All endpoints return either an HTML page (GET) or a redirect (POST). This is a standard Flask MVC pattern.

## Request / Response Contract

### GET routes → render template
```
GET /student/grades
→ 200 OK
→ renders templates/student/grades.html
→ passes: grades=[...], cgpa=3.72
```

### POST routes → redirect (PRG pattern)
```
POST /student/enroll/<course_id>
→ calls stored procedure
→ flash("Enrollment successful.", "success")
→ 302 redirect to /student/courses
```

No route ever renders a template in response to a POST.

---

## Route Reference

### Auth Blueprint — prefix: none

```
GET/POST  /login
  GET  → renders auth/login.html
  POST → reads form: username, password
       → checks fake_users dict (dev mode) or DB (production)
       → sets session: user_id, username, role, entity_id
       → redirects to role dashboard
       → on fail: flash danger + re-render login

GET  /logout
  → session.clear()
  → redirects to /login
```

---

### Student Blueprint — prefix: /student
All routes require: `@login_required`, `@role_required('student')`
All routes read: `session['entity_id']` as `student_id`

```
GET  /student/dashboard
  → queries: enrolled courses for student_id
  → renders: student/dashboard.html
  → passes: student={...}, enrolled=[...]

GET  /student/courses
  → queries: courses NOT enrolled in, with seats_left > 0
  → renders: student/courses.html
  → passes: courses=[{course_id, course_code, course_name, credit_hours, faculty_name, seats_left}]

POST /student/enroll/<int:course_id>
  → calls stored proc: RegisterStudentInCourse(student_id, course_id)
  → flash message from proc OUT param
  → redirects to /student/courses

GET  /student/attendance
  → queries: SELECT * FROM v_attendance_summary WHERE student_id=?
  → renders: student/attendance.html
  → passes: records=[{course_name, total_classes, classes_attended, attendance_percentage}]

GET  /student/grades
  → queries: SELECT * FROM v_student_transcript WHERE student_id=?
  → queries: SELECT cgpa FROM students WHERE student_id=?
  → renders: student/grades.html
  → passes: grades=[...], cgpa=3.72

GET  /student/transcript
  → queries: SELECT * FROM v_student_transcript WHERE student_id=? ORDER BY enrolled_at
  → queries: SELECT * FROM students WHERE student_id=?
  → renders: student/transcript.html
  → passes: transcript=[...], student={...}
```

---

### Faculty Blueprint — prefix: /faculty
All routes require: `@login_required`, `@role_required('faculty')`
All routes read: `session['entity_id']` as `faculty_id`

```
GET  /faculty/dashboard
  → queries: courses WHERE faculty_id=?, enrollment counts
  → renders: faculty/dashboard.html
  → passes: faculty={...}, courses=[...]

GET  /faculty/my_courses
  → queries: courses WHERE faculty_id=?
  → renders: faculty/my_courses.html
  → passes: courses=[...]

GET  /faculty/roster/<int:course_id>
  → queries: SELECT * FROM v_course_roster WHERE course_id=?
  → renders: faculty/roster.html
  → passes: roster=[...], course_name="..."

GET  /faculty/mark_attendance?course_id=<id>
  → queries: enrolled students for course
  → renders: faculty/mark_attendance.html
  → passes: students=[{enrollment_id, student_name}], course_name="..."

POST /faculty/submit_attendance
  → form data: course_id, class_date, status_<enrollment_id> per student
  → loops: INSERT INTO attendance (enrollment_id, class_date, status, marked_by)
  → flash success
  → redirects to /faculty/roster/<course_id>

GET  /faculty/enter_grades/<int:course_id>
  → queries: enrolled students + current grades for course
  → renders: faculty/enter_grades.html
  → passes: students=[{enrollment_id, student_name, marks_obtained, letter_grade}]

POST /faculty/save_grades
  → form data: marks_<enrollment_id> per student
  → loops: UPDATE grades SET marks_obtained=? WHERE enrollment_id=?
  → trigger fires: UpdateLetterGrade() auto-called
  → flash success
  → redirects to /faculty/enter_grades/<course_id>
```

---

### Admin Blueprint — prefix: /admin
All routes require: `@login_required`, `@role_required('admin')`

```
GET  /admin/dashboard
  → queries: COUNT of students, faculty, courses, enrollments
  → renders: admin/dashboard.html
  → passes: stats={students, faculty, courses, enrollments}

GET  /admin/students
  → queries: SELECT students JOIN users
  → renders: admin/students.html
  → passes: students=[...]

POST /admin/add_student
  → form: first_name, last_name, email, program, batch_year, username, password
  → INSERT INTO users (role='student', password=hashed)
  → INSERT INTO students
  → flash success
  → redirects to /admin/students

GET  /admin/faculty
  → queries: SELECT faculty JOIN users
  → renders: admin/faculty.html

POST /admin/add_faculty
  → same pattern as add_student, role='faculty'

GET  /admin/courses
  → queries: SELECT * FROM v_admin_enrollment_report
  → renders: admin/courses.html

POST /admin/create_course
  → form: course_code, course_name, credit_hours, semester, max_capacity
  → INSERT INTO courses
  → redirects to /admin/courses

GET/POST /admin/assign_faculty
  → GET: renders form with course + faculty dropdowns
  → POST: UPDATE courses SET faculty_id=? WHERE course_id=?
  → redirects to /admin/assign_faculty

GET  /admin/reports
  → queries: v_admin_enrollment_report, GPA distribution query, faculty load query
  → renders: admin/reports.html
  → passes: enrollment_report=[...], gpa_dist=[...], faculty_load=[...]
```

---

## Template Variables Reference

Every template variable passed from routes:

| Template | Variable | Type | Source |
|---|---|---|---|
| student/dashboard.html | `student` | dict | students table |
| student/dashboard.html | `enrolled` | list of dicts | enrollments JOIN courses |
| student/courses.html | `courses` | list of dicts | available courses query |
| student/attendance.html | `records` | list of dicts | v_attendance_summary |
| student/grades.html | `grades` | list of dicts | v_student_transcript |
| student/grades.html | `cgpa` | decimal | students.cgpa |
| student/transcript.html | `transcript` | list of dicts | v_student_transcript |
| student/transcript.html | `student` | dict | students table |
| faculty/dashboard.html | `faculty` | dict | faculty table |
| faculty/dashboard.html | `courses` | list of dicts | courses WHERE faculty_id |
| faculty/roster.html | `roster` | list of dicts | v_course_roster |
| faculty/roster.html | `course_name` | str | courses.course_name |
| faculty/mark_attendance.html | `students` | list of dicts | enrollments JOIN students |
| faculty/enter_grades.html | `students` | list of dicts | enrollments JOIN grades |
| admin/dashboard.html | `stats` | dict | COUNT queries |
| admin/students.html | `students` | list of dicts | students JOIN users |
| admin/reports.html | `enrollment_report` | list of dicts | v_admin_enrollment_report |
| admin/reports.html | `gpa_dist` | list of dicts | GPA distribution query |
| admin/reports.html | `faculty_load` | list of dicts | faculty load query |

---

## Form Fields Reference

| Form | Fields | Posts To |
|---|---|---|
| Login | `username`, `password` | /login |
| Enroll | none (course_id in URL) | /student/enroll/<id> |
| Mark Attendance | `course_id`, `class_date`, `status_<enrollment_id>` (×N) | /faculty/submit_attendance |
| Enter Grades | `course_id`, `marks_<enrollment_id>` (×N) | /faculty/save_grades |
| Add Student | `first_name`, `last_name`, `email`, `program`, `batch_year`, `username`, `password` | /admin/add_student |
| Add Faculty | `first_name`, `last_name`, `email`, `department`, `designation`, `username`, `password` | /admin/add_faculty |
| Create Course | `course_code`, `course_name`, `credit_hours`, `semester`, `max_capacity` | /admin/create_course |
| Assign Faculty | `course_id`, `faculty_id` | /admin/assign_faculty |