# Shared Memory

This file is the single source of truth for any AI assistant (GitHub Copilot, Claude, Gemini, etc.) working on this project. Read this file first before making any changes.

---

## What This Project Is
A university academic management system. Flask backend, MySQL database, Jinja2 templates. Three roles: student, faculty, admin. DBMS semester project for a university course.

---

## Current State (update this as work progresses)

### Done
- [x] Full database schema designed (`db/schema.sql`)
- [x] Stored procedures written (`db/stored_procedures.sql`)
- [x] SQL views written (`db/views.sql`)
- [x] Triggers written (`db/triggers.sql`)
- [x] Flask app structure created (`app.py`, blueprints, config, db_connector, decorators)
- [x] All template files scaffolded (empty placeholders exist)
- [x] Frontend templates generated (GitHub Copilot + Google Stitch)
- [x] CSS design system written (`static/css/style.css` — Modern Clean Slate)
- [x] `main.js` written (dark mode, modals, flash dismiss)
- [x] Fake login hardcoded for frontend testing (no DB required)

### Not Done
- [ ] MySQL not yet installed or configured
- [ ] `db/schema.sql` not yet executed against a real DB
- [ ] `db/seed_data.sql` not yet written
- [ ] `blueprints/faculty.py` routes not fully implemented
- [ ] `blueprints/admin.py` routes not fully implemented
- [ ] Real password hashing on add_student / add_faculty not connected
- [ ] Fake login must be replaced with real DB auth before submission

---

## Critical Files — What Each One Does

| File | Purpose | Edit When |
|---|---|---|
| `app.py` | Creates Flask app, registers all 4 blueprints | Adding a new blueprint |
| `config.py` | Reads DB config from .env | Changing DB settings |
| `.env` | Actual secrets (never commit) | Changing DB password or secret key |
| `db_connector.py` | Connection pool + execute_query() helper | Changing DB connection logic |
| `decorators.py` | @login_required, @role_required | Adding new access control logic |
| `blueprints/auth.py` | Login/logout + fake users dict | Implementing real auth |
| `blueprints/student.py` | All student routes | Adding/changing student features |
| `blueprints/faculty.py` | All faculty routes | Adding/changing faculty features |
| `blueprints/admin.py` | All admin routes | Adding/changing admin features |
| `db/schema.sql` | All CREATE TABLE statements | Adding columns or tables |
| `db/stored_procedures.sql` | RegisterStudentInCourse, CalculateStudentGPA, UpdateLetterGrade | Changing business logic |
| `db/views.sql` | 4 SQL views used by Flask routes | Changing what data routes return |
| `static/css/style.css` | Entire design system | Changing visual appearance |
| `static/js/main.js` | Dark mode, modals, flash messages | Adding frontend interactivity |

---

## Known Temporary Hacks (must fix before submission)

### 1. Fake login in `blueprints/auth.py`
```python
fake_users = {
    'student': {'user_id': 1, 'username': 'student', 'role': 'student', 'entity_id': 1},
    'faculty': {'user_id': 2, 'username': 'faculty', 'role': 'faculty', 'entity_id': 1},
    'admin':   {'user_id': 3, 'username': 'admin',   'role': 'admin',   'entity_id': 1},
}
```
**Replace with:** real DB lookup + `check_password_hash()` once MySQL is set up.

### 2. Mock db_connector.py
If the project is running without a database, `db_connector.py` may contain:
```python
def execute_query(query, params=None, fetch=True, many=False):
    return []
```
**Replace with:** the real connection pool version once MySQL is installed.

### 3. Preview route in `app.py`
```python
@app.route('/preview/<template>')
def preview(template):
    ...
```
**Remove** this route before final submission.

---

## Database Setup (run in this order when MySQL is ready)

```
1. Open MySQL Workbench
2. Connect to localhost root
3. Run: db/schema.sql
4. Run: db/stored_procedures.sql
5. Run: db/views.sql
6. Run: db/triggers.sql
7. Run: db/seed_data.sql
8. Update .env with real DB credentials
9. Replace mock db_connector.py with real version
10. Replace fake login in auth.py with real DB auth
```

---

## Design System Rules (for any UI generation)

Design system name: **Modern Clean Slate**

Key rules an AI must follow when generating any new template or component:
- Extend `base.html` — never write standalone HTML for logged-in pages
- Use CSS variables only — never hardcode hex colors
- Sidebar always present for logged-in pages — 240px fixed left
- All interactive elements (buttons, cards) have hover transitions (`0.2s ease`)
- Two font weights only: 400 (body), 700 (headings/labels)
- Status badges are always pill-shaped (`border-radius: 9999px`)
- Modals use `openModal('modal-id')` and `closeModal('modal-id')` from main.js

Dark mode variables are applied via `[data-theme="dark"]` on `<html>`. Toggle is in the sidebar.

---

## Normalization Notes (for project report)

| Table | Normal Form | Reason |
|---|---|---|
| users | BCNF | username → all attrs, no partial deps |
| students | 3NF | student_id → all, no transitive deps |
| faculty | 3NF | faculty_id → all |
| courses | 3NF | course_id → all; faculty_id is FK not transitive dep |
| enrollments | BCNF | (student_id, course_id) → enrollment_id |
| attendance | BCNF | (enrollment_id, class_date) → status |
| grades | BCNF | enrollment_id → all grade attrs |

Why `users` is separate from `students`/`faculty`: storing auth fields (password, role) with personal/academic fields would create a relation with mixed concerns and potential update anomalies — separating satisfies 2NF and improves security.

---

## GPA Grading Scale

| Marks % | Letter | Grade Points |
|---|---|---|
| ≥ 90 | A | 4.00 |
| ≥ 85 | A- | 3.70 |
| ≥ 80 | B+ | 3.30 |
| ≥ 75 | B | 3.00 |
| ≥ 70 | B- | 2.70 |
| ≥ 65 | C+ | 2.30 |
| ≥ 60 | C | 2.00 |
| < 60 | F | 0.00 |

GPA formula: `SUM(grade_points × credit_hours) / SUM(credit_hours)` — implemented in `CalculateStudentGPA` stored procedure.

---

## Environment Variables (.env)

```
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=your_mysql_root_password
DB_NAME=smart_campus
```

---

## How to Run (frontend-only mode, no DB)

```bash
cd smart_campus
venv\Scripts\activate
set FLASK_APP=app.py
set FLASK_DEBUG=1
python app.py
# Open http://127.0.0.1:5000
# Login: student/1234  faculty/1234  admin/1234
```