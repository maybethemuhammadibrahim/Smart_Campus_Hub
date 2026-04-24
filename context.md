# Smart Campus Hub — Project Context (Core)

> **Authoritative AI prompt context.** Keep ≤150 lines. Operational facts only.
> Full reference: `README.md` | SQL artifacts: `db/*.sql`
> **Migration status:** Schema refactor complete. All three role modules (student / faculty / admin) fully migrated.

---

## 1. Overview

| Item | Value |
|------|-------|
| Product | Smart Campus Hub — Academic Management System |
| Domain | Higher-education ERP (students, faculty, courses, grades, attendance) |
| Language | Python 3.11+ |
| Backend | Flask 3.x (Blueprint-based) |
| Database | MySQL 8.x (InnoDB) via `mysql-connector-python` |
| Architecture | Layered Flask app + SQL-first data layer (raw SQL, no ORM) |
| Auth Model | Session-based + role-based access (student/faculty/admin) |
| UI | HTML5 + Vanilla CSS + Vanilla JS (responsive, dark-mode capable) |

---

## 2. Directory Structure

```text
smart_campus/
├── app.py                    # Flask app bootstrap + blueprint registration
├── config.py                 # Env-driven runtime config
├── db_connector.py           # MySQL connection pool + execute helpers
├── decorators.py             # @login_required + @role_required
├── requirements.txt          # Python dependencies
├── context.md                # This file
├── todo.md                   # Migration action plan + regression checklist
├── .env                      # DB + SECRET_KEY config
├── blueprints/
│   ├── auth.py               # Login/logout/session role routing
│   ├── student.py            # Student routes  [MIGRATED ✓]
│   ├── faculty.py            # Faculty routes  [MIGRATED ✓]
│   └── admin.py              # Admin routes    [MIGRATED ✓]
├── db/
│   ├── schema.sql            # Core tables + constraints + indexes
│   ├── stored_procedures.sql # RegisterStudentInCourse, CalculateStudentGPA, UpdateLetterGrade
│   ├── views.sql             # Reporting/query abstraction views
│   ├── triggers.sql          # Validation + audit triggers
│   ├── seed_data.sql         # Demo/academic seed dataset
│   └── queries/              # Role-specific SQL reference queries
├── templates/                # Jinja2 templates by role
└── static/
    ├── css/style.css         # Global design system
    └── js/main.js            # Client-side interaction logic
```

---

## 3. Database

Engine: **MySQL 8.x InnoDB** | Access: pooled connections via `db_connector.py` (pool size 5).

**Core entities (10):** `users`, `students`, `faculty`, `courses`, `semesters`, `course_sections`, `enrollments`, `attendance`, `grades`, `audit_log`.

### Schema Quick Reference (post-refactor — authoritative)

| Table | Key columns / notes |
|-------|---------------------|
| `users` | `password VARCHAR(255)` — **column is `password`, NOT `password_hash`** |
| `students` | No `cgpa` column — CGPA computed via `v_student_cgpa` view |
| `courses` | **Catalog only:** `course_id, course_code, course_name, credit_hours` — **no** `semester`, `faculty_id`, `max_capacity` |
| `semesters` | `semester_id, name UNIQUE, start_date, end_date, is_active`; CHECK `end_date > start_date` |
| `course_sections` | `section_id, course_id, semester_id, faculty_id, section_code, max_capacity`; UNIQUE `(course_id, semester_id, section_code)`; FKs to `courses`, `semesters`, `faculty` |
| `enrollments` | `student_id, section_id` — **FK is `section_id` (not `course_id`)**; UNIQUE `(student_id, section_id)` |
| `attendance` | `marked_by INT` → FK to `users(user_id)` ON DELETE SET NULL |
| `audit_log` | `changed_by INT` → FK to `users(user_id)` ON DELETE SET NULL |
| `grades` | UNIQUE on `enrollment_id`; `idx_grades_enrollment` removed (superseded by UNIQUE) |

### Canonical Join Path (use in ALL queries touching a course)

```sql
FROM enrollments e
JOIN course_sections cs ON e.section_id   = cs.section_id
JOIN courses        c  ON cs.course_id    = c.course_id
LEFT JOIN faculty   f  ON cs.faculty_id   = f.faculty_id
LEFT JOIN semesters sm ON cs.semester_id  = sm.semester_id
```

### section_id / course_id Aliasing Convention (Faculty module)

`_faculty_courses()` returns `cs.section_id AS course_id`. All faculty route URL params and template refs named `course_id` carry **section_id values**. `_owns_course()` queries `course_sections` not `courses`. This keeps all URLs stable.

### Views (canonical — do not bypass)

| View | Purpose |
|------|---------|
| `v_student_transcript` | Full academic record per student (joins via `course_sections`) |
| `v_attendance_summary` | Attendance % per student per section |
| `v_course_roster` | Students enrolled per section — faculty use |
| `v_admin_enrollment_report` | Section fill rates — admin use; columns: `section_id`, `section_code`, `semester_name`, `faculty_name`, `max_capacity`, `enrolled_count`, `seats_remaining`, `fill_percentage` |
| `v_student_cgpa` | **Computed CGPA** from `completed` enrollments + grades + credit hours |

### Integrity Rules

- Future-date attendance blocked by **triggers** on INSERT and UPDATE (`trg_attendance_before_insert`, `trg_attendance_before_update`)
- Marks range enforced by triggers on INSERT and UPDATE (`trg_grade_before_insert`, `trg_grade_before_update`)
- `RegisterStudentInCourse(p_student_id, p_section_id, ...)` — SP enforces capacity and duplicate enrollment
- `students.cgpa` does **not** exist — never SELECT or UPDATE it; always use `v_student_cgpa`

---

## 4. Domain Rules

**Authentication & Roles**
1. Every login resolves to one role: `student` / `faculty` / `admin`
2. Session stores `user_id`, `username`, `role`, `entity_id`
3. All protected routes require `@login_required`; role routes require `@role_required`

**Enrollment**
1. Student–section M:N resolved via `enrollments(student_id, section_id)`
2. Uniqueness: `(student_id, section_id)` — not course-level
3. Capacity checked in `RegisterStudentInCourse` SP against `course_sections.max_capacity`

**Attendance**
1. One row per `(enrollment_id, class_date)` — UNIQUE enforced
2. Future dates blocked by DB triggers (INSERT + UPDATE)
3. `marked_by` must be a valid `users.user_id` (FK enforced)

**Grades & GPA**
1. `marks_obtained` within `[0, total_marks]`; `grade_points` within `[0.00, 4.00]`
2. `UpdateLetterGrade` SP + triggers keep letter grade in sync
3. CGPA is **never stored** — always read from `v_student_cgpa`

**Auditability**
1. Grade and attendance mutations logged to `audit_log` by triggers (non-negotiable)
2. `changed_by` and `marked_by` are `users.user_id` values

---

## 5. Code Standards (enforced)

1. MySQL placeholders `%s` only — never string interpolation
2. No ORM; SQL explicit and centralized
3. Authorization before mutation (`role_required`, ownership checks)
4. Multi-step writes wrapped in transaction handling + rollback
5. Business rules server-side first; UI validation secondary
6. DB constraints/triggers are source of truth for integrity
7. Avoid duplicating logic already in SP/view
8. Session keys and role names stay consistent across blueprints
9. Route handlers return least-privilege data by role
10. Changes to grades/attendance must retain audit-log compatibility

---

## 6. Key Architectural Decisions

| Item | Status |
|------|--------|
| Flask Blueprints by domain (`auth/student/faculty/admin`) | KEEP |
| Raw SQL + MySQL connector (no ORM) | KEEP |
| DB-level governance (CHECK, triggers, SPs, views) | KEEP |
| Connection pooling in app layer (size 5 baseline) | KEEP |
| Session-based auth + decorator RBAC | KEEP |
| Faculty ownership guard via `course_sections` | ENFORCED (updated) — Faculty can teach multiple sections of the same course. |
| Faculty Workload Limit | ENFORCED (6 sections/sem max default). Edit via `config.py:MAX_COURSES_PER_FACULTY` + `db/triggers.sql` |
| Stored procedures for enrollment and GPA workflows | KEEP |
| Audit logging for grade/attendance mutations | KEEP (non-negotiable) |
| `courses` as catalog only; offering data in `course_sections` | ENFORCED |
| CGPA computed via `v_student_cgpa` (not stored in `students`) | ENFORCED |
| `section_id` aliased as `course_id` in faculty helper | CONVENTION — do not break |

---

## 7. Canonical Routes

**Auth:** `/login`, `/logout`
**Student:** `/student/dashboard`, `/student/courses`, `/student/enroll/<id>`, `/student/attendance`, `/student/grades`, `/student/transcript`
**Faculty:** `/faculty/dashboard`, `/faculty/my-courses`, `/faculty/roster/<id>`, `/faculty/attendance/<id>`, `/faculty/attendance/submit`, `/faculty/attendance/history/<id>`, `/faculty/grades/<id>`, `/faculty/grades/save`, `/faculty/analytics/<id>`, `/faculty/profile`, `/faculty/profile/update`, `/faculty/api/course-students/<id>`
**Admin:** `/admin/dashboard`, `/admin/students`, `/admin/students/add`, `/admin/faculty`, `/admin/faculty/add`, `/admin/courses`, `/admin/courses/create`, `/admin/reports`