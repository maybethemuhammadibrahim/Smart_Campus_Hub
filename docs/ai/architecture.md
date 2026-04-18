# Architecture

Use this file for app structure, database shape, and route inventory.

## System
Browser -> Flask (WSGI) -> MySQL

## Core files
- `app.py`: creates app and registers blueprints
- `config.py`: reads DB config from `.env`
- `db_connector.py`: query helper / connection access
- `decorators.py`: login and role guards
- `blueprints/`: auth, student, faculty, admin route logic
- `db/`: schema, procedures, views, triggers, seed data
- `templates/`: HTML pages
- `static/`: CSS and JS

## Database
| Table | Key fields |
|---|---|
| users | user_id, username, password, role, is_active |
| students | student_id, user_id, first_name, last_name, email, program, batch_year, cgpa |
| faculty | faculty_id, user_id, first_name, last_name, email, department, designation |
| courses | course_id, course_code, course_name, credit_hours, semester, faculty_id, max_capacity |
| enrollments | enrollment_id, student_id, course_id, enrolled_at, status |
| attendance | attendance_id, enrollment_id, class_date, status, marked_by |
| grades | grade_id, enrollment_id, marks_obtained, total_marks, letter_grade, grade_points |

## Relations
- `users` 1:1 `students` / `faculty`
- `students` 1:M `enrollments`
- `courses` 1:M `enrollments`
- `enrollments` 1:1 `grades`
- `enrollments` 1:M `attendance`
- `faculty` 1:M `courses`

## DB objects
| Type | Name | Use |
|---|---|---|
| Procedure | `RegisterStudentInCourse` | enroll with capacity/duplicate checks |
| Procedure | `CalculateStudentGPA` | update student CGPA |
| Procedure | `UpdateLetterGrade` | derive grade from marks |
| View | `v_student_transcript` | student transcript/grades |
| View | `v_attendance_summary` | attendance summary |
| View | `v_course_roster` | faculty roster |
| View | `v_admin_enrollment_report` | admin reports |
| Trigger | `trg_grade_after_update` | auto-refresh grade labels |

## Routes
| Blueprint | Main routes |
|---|---|
| auth | `/login`, `/logout` |
| student | `/student/dashboard`, `/student/courses`, `/student/enroll/<course_id>`, `/student/attendance`, `/student/grades`, `/student/transcript` |
| faculty | `/faculty/dashboard`, `/faculty/my-courses`, `/faculty/roster`, `/faculty/roster/<course_id>`, `/faculty/attendance`, `/faculty/attendance/submit`, `/faculty/grades`, `/faculty/grades/save` |
| admin | `/admin/dashboard`, `/admin/students`, `/admin/faculty`, `/admin/courses`, `/admin/reports`, `/admin/students/add`, `/admin/faculty/add`, `/admin/courses/create` |

## Session
Set on login: `user_id`, `username`, `role`, `entity_id`.
