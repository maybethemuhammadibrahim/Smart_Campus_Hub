# Schema Migration Action Plan (Module-wise)

> **Status:** Schema refactor complete. All three role modules migrated. ✅
> **Remaining work:** Run post-migration regression across all three modules before merge.
> **Rule:** Do NOT modify any SQL files. Fix only Python blueprints + Jinja templates.

---

## ADMIN

### Impact Summary
`admin.py` contained 6 crash points referencing removed columns.

### Required File Update Checklist
- [x] `blueprints/admin.py` — all 6 queries fixed
- [x] `templates/admin/students.html` — CGPA sourced via `v_student_cgpa` LEFT JOIN (key `cgpa` unchanged in template)
- [x] `templates/admin/courses.html` — shows `section_code` + `semester_name`; create modal adds Section Code field
- [x] `templates/admin/dashboard.html` — create-course modal: Section Code field added; credit_hours max corrected to 3
- [x] `templates/admin/reports.html` — no template change needed (Python-side fixed)

### Query Migration Rules (applied)
| Route | Old | New |
|-------|-----|-----|
| `GET /admin/dashboard` | `enrollments.course_id` → `courses` | `enrollments.section_id` → `course_sections` → `courses` |
| `GET /admin/students` | `students.cgpa` direct | `v_student_cgpa` LEFT JOIN |
| `GET /admin/courses` | hand-rolled JOIN on `courses.faculty_id`, `c.semester`, `c.max_capacity` | `v_admin_enrollment_report` |
| `POST /admin/courses/create` | single INSERT into `courses` with `semester`/`max_capacity` | 3-step: resolve `semesters` → upsert `courses` → INSERT `course_sections` |
| `GET /admin/reports` GPA | `students.cgpa` GROUP BY | `v_student_cgpa` GROUP BY |
| `GET /admin/reports` faculty load | `courses.faculty_id`, `enrollments.course_id` | `course_sections.faculty_id`, `enrollments.section_id` |

### Definition of Done — ADMIN ✅
- [x] `/admin/dashboard` loads; recent activity shows course codes
- [x] `/admin/students` lists students with computed CGPA
- [x] `/admin/courses` shows section + semester columns; no `Unknown column` errors
- [x] Create course inserts into `courses` AND `course_sections`
- [x] `/admin/reports` GPA distribution uses `v_student_cgpa`; faculty load uses `course_sections`

---

## FACULTY

### Impact Summary
`faculty.py` contained 7 crash points; CGPA write-back was also fatal.

### Required File Update Checklist
- [x] `blueprints/faculty.py` — all helpers and routes fixed
- [x] `templates/faculty/my_courses.html` — `course.semester` → `course.semester_name`
- [x] `templates/faculty/dashboard.html` — no change needed (keys fed from Python dict)
- [x] `templates/faculty/roster.html` — no change needed
- [x] `templates/faculty/mark_attendance.html` — no change needed (course_id param preserved)
- [x] `templates/faculty/attendance_history.html` — no change needed
- [x] `templates/faculty/enter_grades.html` — no change needed
- [x] `templates/faculty/analytics.html` — no change needed
- [x] `templates/faculty/profile.html` — no change needed

### Query Migration Rules (applied)
| Function/Route | Old | New |
|---------------|-----|-----|
| `_faculty_courses()` | `courses c WHERE c.faculty_id=%s` + `e.course_id` | `course_sections cs WHERE cs.faculty_id=%s` + `e.section_id`; returns `cs.section_id AS course_id` |
| `_owns_course()` | `courses WHERE course_id=%s AND faculty_id=%s` | `course_sections WHERE section_id=%s AND faculty_id=%s` |
| `dashboard()` stats | `JOIN courses c ON e.course_id … WHERE c.faculty_id=%s` | `JOIN course_sections cs ON e.section_id … WHERE cs.faculty_id=%s` |
| All roster/attendance/grades/analytics | `WHERE e.course_id=%s` | `WHERE e.section_id=%s` |
| `save_grades()` CGPA write-back | `UPDATE students SET cgpa = …` | **Removed** (CGPA is view-computed) |
| `enter_grades()` + `analytics()` course name | `SELECT course_name FROM courses WHERE course_id=%s` | `SELECT c.course_name FROM course_sections cs JOIN courses c … WHERE cs.section_id=%s` |

### Definition of Done — FACULTY ✅
- [x] `/faculty/dashboard` loads; stat cards show correct counts
- [x] `/faculty/my-courses` shows sections with semester name
- [x] `_owns_course()` guards section ownership correctly
- [x] Roster loads students filtered by `section_id`
- [x] Attendance mark/submit uses `section_id`; `marked_by` is `user_id`
- [x] Grade save uses `section_id`; no `cgpa` write-back attempted
- [x] Analytics page loads per section
- [x] `/faculty/api/course-students/<id>` returns JSON (used by JS dynamic switching)

---

## STUDENT

### Impact Summary
All fixes applied in the first migration run.

### Required File Update Checklist
- [x] `blueprints/student.py` — all routes fixed; attendance + grades routes support `?semester=` filter; transcript route groups by semester with SGPA
- [x] `templates/student/dashboard.html` — `student.cgpa` → `cgpa` variable; Section + Semester columns added
- [x] `templates/student/courses.html` — Section column added
- [x] `templates/student/attendance.html` — Section + Semester columns added; semester dropdown filter
- [x] `templates/student/grades.html` — Section + Semester columns added; semester dropdown filter; CGPA stays cumulative
- [x] `templates/student/transcript.html` — semester-grouped cards with per-semester table + summary (Semester Credits | Total Credits | Semester GPA); CGPA in top info bar; Email removed; bottom CGPA card removed

### Student UI Phases — Completion Status

| Phase | Status | Summary |
|-------|--------|----------|
| Phase 1 — Consistency | ✅ Done | Section + Semester badge columns added to all 5 student pages |
| Phase 2 — Semester Filters | ✅ Done | `?semester=` dropdown on attendance + grades; parameterized SQL; invalid semester → graceful empty state |
| Phase 3 — Transcript Grouping | ✅ Done | Semester-grouped cards; per-semester SGPA summary; cumulative total credits; CGPA moved to info bar |

### Definition of Done — STUDENT ✅
- [x] `/student/dashboard` loads; enrolled table shows section, semester, faculty; CGPA card shows value
- [x] `/student/courses` shows available sections with section column, semester, seats
- [x] Enroll flow completes; SP called with `section_id`
- [x] `/student/attendance` shows attendance per section with section/semester badges; semester dropdown filters results
- [x] `/student/grades` shows computed CGPA (cumulative); semester dropdown filters grade table
- [x] `/student/transcript` groups by semester; each card has table + summary row; CGPA in top info bar

---

## Post-Migration Regression Checklist

Run these before any merge or deployment.

### Auth / Shared
- [ ] Log in as each of the three roles — no 500 on dashboard for any role
- [ ] Log out and back in — session cleared correctly
- [ ] Verify `users` table column is `password` (not `password_hash`) — auth still works

### Student
- [ ] `/student/dashboard` — enrolled courses list with section, semester, faculty; CGPA card shows value
- [ ] `/student/courses` — available sections visible; section badge, seats_left correct; semester shown
- [ ] Enroll in a section → flash "Enrollment successful." → section disappears from available list
- [ ] `/student/attendance` — attendance % per section with section/semester badges; semester dropdown filters correctly
- [ ] `/student/attendance?semester=NonExistent` — graceful empty state, no 500
- [ ] `/student/grades` — letter grades table + semester dropdown filter; CGPA card shows cumulative (unchanged by filter)
- [ ] `/student/grades?semester=NonExistent` — graceful empty state, no 500
- [ ] `/student/transcript` — grouped by semester; each card has summary row (Semester Credits | Total Credits | Semester GPA); CGPA in top info bar; no bottom CGPA box
- [ ] Print button on transcript works

### Faculty
- [ ] `/faculty/dashboard` — stat cards: courses, students, avg attendance, avg marks
- [ ] `/faculty/my-courses` — course cards show semester name badge
- [ ] Roster for a section — students listed with attendance % and grade
- [ ] Mark attendance → submit → flash confirms count; attendance appears in history
- [ ] Attendance history — records and date summary render
- [ ] Enter grades → save → flash confirms count; **no** `Unknown column 'cgpa'` error
- [ ] `/faculty/analytics/<id>` — grade distribution, top students, at-risk list render
- [ ] `GET /faculty/api/course-students/<id>` — returns JSON list (JS dynamic switching)
- [ ] Profile update → email/department/designation saved

### Admin
- [ ] `/admin/dashboard` — stat cards correct; recent activity shows student + course code
- [ ] `/admin/students` — CGPA column shows computed value (or `0.00`)
- [ ] Add student → appears in list with `0.00` CGPA
- [ ] Edit student → changes saved
- [ ] `/admin/faculty` — renders without error
- [ ] Add faculty → appears in faculty list
- [ ] `/admin/courses` — shows `Section`, `Semester`, `Faculty`, `Enrolled/Capacity`
- [ ] Create course (new code) → flash "Course created successfully." → appears in list
- [ ] Create course (existing code, new semester) → new section row inserted without duplicate error on courses
- [ ] `/admin/reports` — enrollment report, GPA distribution, faculty load all render

### Database Integrity
- [ ] `SELECT * FROM v_student_cgpa;` — returns rows for students with completed grades
- [ ] `SHOW CREATE TABLE enrollments;` — FK is on `section_id`, no `course_id` column
- [ ] Mark future-date attendance (e.g. `2099-01-01`) → trigger blocks with error message
- [ ] Verify `audit_log` has rows after a grade update and an attendance update

---

## Open Risks / Follow-ups

| Risk | Detail | Severity |
|------|--------|----------|
| `create_course` semester date defaults | New semesters created via admin form get `CURDATE()` → `CURDATE()+6mo` as placeholder dates. Dates should be set manually or via a future semester-management form. | Low |
| Faculty course ownership after admin reassignment | If admin reassigns a section to a different faculty, old faculty will immediately lose access (correct behavior). Confirm UI communicates this. | Low |
| `section_id AS course_id` aliasing | All faculty URL params carry `section_id` values under the `course_id` name. If any future query uses both simultaneously, the alias will be ambiguous. Document before adding multi-section features. | Medium |
