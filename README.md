# 🎓 Smart Campus Hub — Academic Management System

A full-stack **Academic Management System** built with **Flask + MySQL** for managing students, faculty, courses, grades, and attendance. This project demonstrates advanced database concepts including normalization, stored procedures, triggers, views, CHECK constraints, and connection pooling..

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Database Design](#-database-design)
- [Module Breakdown](#-module-breakdown)
- [Faculty Portal Deep Dive](#-faculty-portal-deep-dive)
- [Route Reference](#-route-reference)
- [Database Objects Reference](#-database-objects-reference)
- [Setup Guide](#-setup-guide)
- [Security Features](#-security-features)
- [How to Improve](#-how-to-improve)
- [DBMS Syllabus Coverage](#-dbms-syllabus-coverage)

---

## 🌟 Overview

**Smart Campus Hub** is a role-based academic management platform with three portals:

| Portal | Users | Core Features |
|--------|-------|---------------|
| **Student Portal** | Students | View courses, enroll, check grades/attendance with semester filters, semester-grouped transcript |
| **Faculty Portal** | Professors | Manage courses, mark attendance, enter grades, view analytics |
| **Admin Portal** | Administrators | Manage users, courses, enrollment reports, GPA distribution |

### Key Highlights
- ✅ **Role-Based Access Control** — Students, Faculty, and Admin each see only their relevant data
- ✅ **Database-Level Validation** — CHECK constraints, triggers, and stored procedures enforce data integrity
- ✅ **Audit Logging** — Grade and attendance changes are tracked in an audit_log table
- ✅ **Connection Pooling** — MySQL connection pool (5 connections) for efficient resource usage
- ✅ **Premium UI** — Modern design with dark mode, micro-animations, glassmorphism effects
- ✅ **Responsive Design** — Works on desktop, tablet, and mobile

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, Flask 3.x |
| **Database** | MySQL 8.x (InnoDB engine) |
| **ORM/Connector** | `mysql-connector-python` (raw SQL, no ORM) |
| **Authentication** | `werkzeug.security` (bcrypt password hashing) |
| **Frontend** | HTML5, Vanilla CSS, Vanilla JavaScript |
| **Font** | Inter (Google Fonts) |
| **Environment** | `python-dotenv` for `.env` configuration |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Client)                  │
│         HTML Templates + CSS + JavaScript            │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP Requests
┌──────────────────────▼──────────────────────────────┐
│                  Flask Application                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ auth_bp  │  │faculty_bp│  │ admin_bp │          │
│  │ (login/  │  │(courses, │  │(manage   │          │
│  │  logout) │  │ grades,  │  │ students,│          │
│  └────┬─────┘  │ attend.) │  │ faculty) │          │
│       │        └────┬─────┘  └────┬─────┘          │
│  ┌────▼─────────────▼─────────────▼─────┐          │
│  │        decorators.py                  │          │
│  │   @login_required  @role_required     │          │
│  └────────────────┬──────────────────────┘          │
│  ┌────────────────▼──────────────────────┐          │
│  │        db_connector.py                │          │
│  │   Connection Pool (5 connections)     │          │
│  │   execute_query() / call_procedure()  │          │
│  └────────────────┬──────────────────────┘          │
└───────────────────┼──────────────────────────────────┘
                    │ MySQL Protocol
┌───────────────────▼──────────────────────────────────┐
│              MySQL 8.x Database                       │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐  │
│  │ Tables  │ │  Views   │ │Triggers │ │Stored    │  │
│  │ (10)    │ │  (5)     │ │ (7)     │ │Procs (3) │  │
│  └─────────┘ └──────────┘ └─────────┘ └──────────┘  │
└──────────────────────────────────────────────────────┘
```

### Project Structure

```
smart_campus/
├── app.py                    # Flask app factory, blueprint registration
├── config.py                 # DB credentials from .env
├── db_connector.py           # MySQL connection pool + query helpers
├── decorators.py             # @login_required, @role_required
├── requirements.txt          # Python dependencies
├── .env                      # Local secrets (DB_HOST, DB_USER, etc.)
│
├── blueprints/
│   ├── __init__.py
│   ├── auth.py               # Login/logout with password hashing
│   ├── student.py            # Student portal routes
│   ├── faculty.py            # Faculty portal routes (13 routes)
│   └── admin.py              # Admin portal routes
│
├── db/
│   ├── schema.sql            # 10 tables with CHECK constraints + indexes
│   ├── stored_procedures.sql # 3 stored procedures
│   ├── views.sql             # 5 SQL views
│   ├── triggers.sql          # 7 triggers (validation + audit)
│   ├── seed_data.sql         # Sample data (10 users, 8 courses, etc.)
│   └── queries/
│       ├── student_queries.sql
│       ├── faculty_queries.sql
│       └── admin_queries.sql
│
├── templates/
│   ├── base.html             # Master layout with sidebar navigation
│   ├── auth/login.html
│   ├── student/              # 6 student templates
│   ├── faculty/              # 8 faculty templates ⭐
│   │   ├── dashboard.html
│   │   ├── my_courses.html
│   │   ├── roster.html
│   │   ├── mark_attendance.html
│   │   ├── enter_grades.html
│   │   ├── analytics.html        # NEW: course performance analytics
│   │   ├── attendance_history.html # NEW: historical attendance records
│   │   └── profile.html          # NEW: faculty profile management
│   └── admin/                # 6 admin templates
│
└── static/
    ├── css/style.css         # Premium design system (~1000 lines)
    └── js/main.js            # Dynamic interactions (~300 lines)
```

---

## 🗄 Database Design

### Entity-Relationship Summary

```
users (1) ──── (1) students          [via user_id FK]
users (1) ──── (1) faculty           [via user_id FK]
courses (1) ── (M) course_sections   [catalog course offered in many sections]
faculty (1) ── (M) course_sections   [faculty assigned to sections]
semesters (1) ─ (M) course_sections  [semester contains many sections]
students (M) ─ (M) course_sections   [resolved via enrollments → section_id]
enrollments (1) ── (M) attendance
enrollments (1) ── (1) grades
```

### Tables (10 total)

| # | Table | Purpose | Key Constraints |
|---|-------|---------|----------------|
| 1 | `users` | Authentication & roles | `UNIQUE(username)`, `CHECK(LENGTH(username) >= 3)` |
| 2 | `students` | Student profiles | `CHECK(email LIKE '%@%')` — no stored `cgpa` column |
| 3 | `faculty` | Faculty profiles | `CHECK(email LIKE '%@%')` |
| 4 | `courses` | Course catalog only | `CHECK(credit_hours BETWEEN 1 AND 3)` — no `faculty_id`, `semester`, `max_capacity` |
| 5 | `semesters` | Academic semester registry | `UNIQUE(name)`, `CHECK(end_date > start_date)` |
| 6 | `course_sections` | Course offerings (section per semester) | `UNIQUE(course_id, semester_id, section_code)`; FKs to `courses`, `semesters`, `faculty` |
| 7 | `enrollments` | Student-Section junction | `UNIQUE(student_id, section_id)` — FK to `section_id` |
| 8 | `attendance` | Daily attendance records | `UNIQUE(enrollment_id, class_date)`; future-date blocked by trigger |
| 9 | `grades` | Academic grades | `CHECK(marks_obtained BETWEEN 0 AND total_marks)`, `CHECK(grade_points BETWEEN 0 AND 4)` |
| 10 | `audit_log` | Change tracking | Populated by triggers on grades/attendance |

### Normalization

| Normal Form | How It's Achieved |
|-------------|-------------------|
| **1NF** | All attributes are atomic; no multi-valued attributes |
| **2NF** | Auth data (users table) separated from entity data (students/faculty) — no partial dependencies |
| **3NF** | No transitive dependencies — `cgpa` is fully computed via `v_student_cgpa` view; no derived column stored |
| **BCNF** | Every determinant is a candidate key in all tables |

---

## 📦 Module Breakdown

### 1. Authentication Module (`auth.py`)
- **Login** — Validates credentials against `users` table with bcrypt password verification
- **Session Management** — Stores `user_id`, `username`, `role`, and `entity_id` in Flask session
- **Logout** — Clears session and redirects to login page
- **Role Routing** — Automatically redirects to the correct portal after login

### 2. Student Portal (`student.py`)
- Dashboard with enrolled courses (section + semester badges) and profile info
- Browse and enroll in available courses (via stored procedure)
- View attendance percentage per course with **semester dropdown filter** (via `v_attendance_summary` view)
- View grades with **semester dropdown filter**; CGPA always cumulative (via `v_student_cgpa` view)
- **Semester-grouped academic transcript** with per-semester summary (Semester Credits | Total Credits | Semester GPA)

### 3. Faculty Portal (`faculty.py`) ⭐
- **13 routes** covering course management, grading, attendance, analytics, and profile
- See [Faculty Portal Deep Dive](#-faculty-portal-deep-dive) below

### 4. Admin Portal (`admin.py`)
- Dashboard with system-wide statistics
- Manage students (add/view)
- Manage faculty (add/view)
- Manage courses (create/view with faculty assignment)
- Reports: enrollment stats, GPA distribution, faculty workload

---

## ⭐ Faculty Portal Deep Dive

The Faculty Portal is the most feature-rich module with **13 routes** and **8 templates**.

### Features Overview

| Feature | Route | Description |
|---------|-------|-------------|
| **Dashboard** | `/faculty/dashboard` | Welcome banner, 4 animated stat cards, quick actions, courses table, recent activity feed |
| **My Courses** | `/faculty/my-courses` | Course cards with enrollment progress bars, action buttons |
| **Roster** | `/faculty/roster/<id>` | Student list with search/filter, summary stats, attendance %, grade badges |
| **Mark Attendance** | `/faculty/attendance/<id>` | Color-coded radio buttons, bulk "Mark All" actions, live P/A/L counter, confirmation dialog |
| **Attendance History** | `/faculty/attendance/history/<id>` | Date-wise attendance summaries, searchable detailed records |
| **Enter Grades** | `/faculty/grades/<id>` | Live grade preview (auto-calculates letter grade as you type), unsaved changes indicator, grade scale reference |
| **Analytics** | `/faculty/analytics/<id>` | Grade distribution bar chart, top performers, at-risk students, average stats |
| **Profile** | `/faculty/profile` | View/edit email, department, designation with form validation |

### Dashboard Features
```
┌──────────────────────────────────────────────────────┐
│  Welcome back, Professor Khan!                        │
│  Computer Science — Manage your courses...            │
│  [Assistant Professor]                                │
├──────────────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐    │
│  │  📚 2  │  │  👥 5  │  │ 📋 85% │  │ 📝 82  │    │
│  │Courses │  │Students│  │Avg Att.│  │Avg Mark│    │
│  └────────┘  └────────┘  └────────┘  └────────┘    │
├──────────────────────────────────────────────────────┤
│  Quick: [✅ Mark Attendance] [📝 Grades] [📈 Analytics] │
├───────────────────────┬──────────────────────────────┤
│   Assigned Courses    │    Recent Activity           │
│   CS101 - Intro Prog  │    ✅ Hassan — present CS101 │
│   CS205 - Database    │    📝 Fatima — 91/100 CS205  │
└───────────────────────┴──────────────────────────────┘
```

### Attendance Marking Flow
1. Select course from dropdown (auto-loads students)
2. Choose date (defaults to today)
3. Use **"All Present"** / **"All Absent"** / **"All Late"** bulk buttons
4. Fine-tune individual students with color-coded radio buttons
5. Live counter shows Present/Absent/Late counts in real-time
6. Click submit → confirmation dialog → attendance saved

### Grade Entry Flow
1. Select course from dropdown
2. Enter marks (0–100) for each student
3. **Live preview** shows calculated letter grade as you type
4. Unsaved changes indicator (amber dot) appears when values change
5. Submit → confirmation dialog → grades saved + student CGPAs recalculated

### Analytics Dashboard
- **Stat Cards**: Total students, average marks, highest score, average attendance
- **Grade Distribution**: Animated CSS bar chart (A/B/C/F with color coding)
- **Top 5 Performers**: Table with gold/silver/bronze medals
- **At-Risk Students**: Flagged students with low attendance (<75%) or failing grades

---

## 🔗 Route Reference

### Authentication Routes

| Method | Endpoint | Function |
|--------|----------|----------|
| GET/POST | `/login` | Login page + form handler |
| GET | `/logout` | Clear session, redirect |

### Faculty Routes (13 total)

| Method | Endpoint | Function | Description |
|--------|----------|----------|-------------|
| GET | `/faculty/dashboard` | `dashboard()` | Main dashboard with stats, activity |
| GET | `/faculty/my-courses` | `my_courses()` | List assigned courses |
| GET | `/faculty/roster/<id>` | `roster()` | Student roster for a course |
| GET | `/faculty/attendance/<id>` | `mark_attendance()` | Attendance form |
| POST | `/faculty/attendance/submit` | `submit_attendance()` | Save attendance records |
| GET | `/faculty/attendance/history/<id>` | `attendance_history()` | Past attendance records |
| GET | `/faculty/grades/<id>` | `enter_grades()` | Grade entry form |
| POST | `/faculty/grades/save` | `save_grades()` | Save grades (CGPA auto-computed via view; no write-back) |
| GET | `/faculty/analytics/<id>` | `analytics()` | Course performance analytics |
| GET | `/faculty/profile` | `profile()` | Faculty profile view |
| POST | `/faculty/profile/update` | `update_profile()` | Save profile changes |
| GET | `/faculty/api/course-students/<id>` | `api_course_students()` | JSON API for dynamic loading |

### Student Routes

| Method | Endpoint | Function |
|--------|----------|----------|
| GET | `/student/dashboard` | Student dashboard |
| GET | `/student/courses` | Available courses |
| POST | `/student/enroll/<id>` | Enroll in course |
| GET | `/student/attendance` | Attendance summary (supports `?semester=`) |
| GET | `/student/grades` | Grades + CGPA (supports `?semester=`) |
| GET | `/student/transcript` | Semester-grouped transcript |
| GET | `/student/profile` | Student profile |
| POST | `/student/change-password` | Change password |

### Admin Routes

| Method | Endpoint | Function |
|--------|----------|----------|
| GET | `/admin/dashboard` | Admin dashboard |
| GET | `/admin/students` | Student management |
| POST | `/admin/students/add` | Add new student |
| GET | `/admin/faculty` | Faculty management |
| POST | `/admin/faculty/add` | Add new faculty |
| GET | `/admin/courses` | Course management |
| POST | `/admin/courses/create` | Create course |
| GET | `/admin/reports` | Reports & analytics |

---

## 🗃 Database Objects Reference

### Views (5)

| View | Purpose | Used By |
|------|---------|---------|
| `v_student_transcript` | Full academic record with grades (joins via `course_sections`) | Student grades/transcript |
| `v_attendance_summary` | Attendance % per enrollment per section | Student attendance, Faculty roster |
| `v_course_roster` | Students enrolled in each section | Faculty roster |
| `v_admin_enrollment_report` | Section fill rates (`section_id`, `section_code`, `semester_name`, `max_capacity`) | Admin reports |
| `v_student_cgpa` | Computed CGPA from completed enrollments + grades + credit hours | Student dashboard/transcript/grades, Admin reports |

### Stored Procedures (3)

| Procedure | Parameters | Purpose |
|-----------|-----------|---------|
| `RegisterStudentInCourse` | IN student_id, section_id; OUT message, success | Enrolls student in a section with capacity check |
| `CalculateStudentGPA` | IN student_id; OUT gpa | Computes weighted GPA |
| `UpdateLetterGrade` | IN enrollment_id | Sets letter grade from marks |

### Triggers (7)

| Trigger | Event | Purpose |
|---------|-------|---------|
| `trg_grade_before_insert` | BEFORE INSERT on grades | Validates marks range |
| `trg_grade_before_update` | BEFORE UPDATE on grades | Validates marks range |
| `trg_grade_after_update` | AFTER UPDATE on grades | Auto-updates letter grade |
| `trg_grade_audit_update` | AFTER UPDATE on grades | Logs changes to audit_log |
| `trg_attendance_audit_update` | AFTER UPDATE on attendance | Logs changes to audit_log |
| `trg_attendance_before_insert` | BEFORE INSERT on attendance | Blocks future-date attendance |
| `trg_attendance_before_update` | BEFORE UPDATE on attendance | Blocks future-date on edits |

### CHECK Constraints (7)

| Table | Constraint | Rule |
|-------|-----------|------|
| users | `chk_username_len` | `LENGTH(username) >= 3` |
| students | `chk_student_email` | `email LIKE '%@%'` |
| faculty | `chk_faculty_email` | `email LIKE '%@%'` |
| courses | `chk_credit_hours` | `credit_hours BETWEEN 1 AND 3` |
| semesters | `chk_semester_dates` | `end_date > start_date` |
| grades | `chk_marks_obtained` | `marks_obtained BETWEEN 0 AND total_marks` |
| grades | `chk_total_marks` | `total_marks > 0` |
| grades | `chk_grade_points` | `grade_points BETWEEN 0.00 AND 4.00` |

> **Note:** `attendance.class_date <= CURDATE()` is enforced by triggers (INSERT + UPDATE) rather than a CHECK constraint, because `CURDATE()` is non-deterministic and cannot be used in MySQL CHECK constraints.

---

## 🚀 Setup Guide

### Prerequisites
- **Python 3.11+** — [Download](https://python.org/downloads)
- **MySQL 8.x** — [Download](https://dev.mysql.com/downloads/installer/)
- **MySQL Workbench** (optional, for visual management)

### Step 1: Clone & Install Dependencies

```bash
git clone <repository-url>
cd smart_campus

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file in the project root:

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=your_mysql_password
DB_NAME=smart_campus
SECRET_KEY=your-secret-key-here
```

### Step 3: Initialize Database

Execute SQL scripts in **this exact order** via MySQL Workbench or CLI:

```bash
mysql -u root -p < db/schema.sql
mysql -u root -p < db/stored_procedures.sql
mysql -u root -p < db/views.sql
mysql -u root -p < db/triggers.sql
mysql -u root -p < db/seed_data.sql
```

### Step 4: Run the Application

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

### Step 5: Test Login Credentials

| Username | Role | Notes |
|----------|------|-------|
| `f_khan` | Faculty | Has CS101 and CS205 assigned |
| `f_mehmood` | Faculty | Has IT220 and IS310 assigned |
| `s_hassan` | Student | Enrolled in 3 courses |
| `admin_ali` | Admin | Full system access |

> **Note:** The seed data uses bcrypt-style hashes. If you need to log in, either update the passwords in `seed_data.sql` with real hashes generated by `werkzeug.security.generate_password_hash('your_password')`, or temporarily disable the hash check in `auth.py`.

---

## 🔒 Security Features

| Feature | Implementation |
|---------|---------------|
| **Password Hashing** | `werkzeug.security.generate_password_hash` + `check_password_hash` (bcrypt) |
| **Session-Based Auth** | Flask session with server-side storage |
| **Role-Based Access** | `@login_required` and `@role_required` decorators on all routes |
| **Course Ownership** | `_owns_course()` check prevents faculty from accessing other faculty's courses |
| **Input Validation** | Server-side validation on all form inputs + DB-level CHECK constraints |
| **SQL Injection Prevention** | Parameterized queries (`%s` placeholders) throughout |
| **Error Handling** | try/except with rollback on all database operations |
| **Audit Trail** | `audit_log` table tracks grade and attendance modifications |

---

## 🚀 How to Improve

### Short-Term Improvements

1. **CSRF Protection** — Add `flask-wtf` for CSRF tokens on all forms:
   ```python
   pip install flask-wtf
   # In app.py: from flask_wtf.csrf import CSRFProtect; csrf = CSRFProtect(app)
   # In templates: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
   ```

2. **Password Reset** — Add email-based password reset flow using `flask-mail`

3. **Pagination** — Large datasets need pagination on student/course lists:
   ```sql
   SELECT * FROM students LIMIT 20 OFFSET 0;
   ```

4. **File Export** — Add CSV/PDF export for roster and transcripts using `csv` module or `reportlab`

5. **Real-Time Notifications** — Use Flask-SocketIO for live updates when grades are posted

### Medium-Term Improvements

6. **REST API** — Build a full REST API (`/api/v1/...`) for mobile app integration

7. **Email Notifications** — Send emails when grades are posted or attendance drops below threshold

8. **Course Scheduling** — Add timetable management with room allocation

9. **Assignment Management** — Allow faculty to create, distribute, and grade assignments

10. **Discussion Forum** — Add a per-course discussion board

### Long-Term / Advanced

11. **OAuth2 / SSO** — Integrate Google/Microsoft SSO for authentication

12. **Docker Deployment** — Containerize the app with Docker + docker-compose

13. **Caching** — Add Redis caching for frequently accessed data (dashboards)

14. **Data Visualization** — Integrate Chart.js for interactive analytics charts

15. **Mobile App** — Build a Flutter/React Native mobile app consuming the REST API

---

## 📖 DBMS Syllabus Coverage

| Syllabus Topic | Where It Appears |
|---|---|
| **Ch.1** — DB characteristics, DBMS advantages | Project uses structured relational DB vs flat files |
| **Ch.2** — Three-schema architecture | External (UI templates), Conceptual (ERD), Internal (MySQL InnoDB storage) |
| **Ch.3** — ER Diagram, entity types | ERD derivable from schema.sql — 8 entities with relationships |
| **Ch.5** — Relational model, constraints, FKs | `schema.sql` — every FK, UNIQUE, ENUM, CHECK, NOT NULL |
| **Ch.6** — DDL, DML, SQL | `schema.sql` (DDL), `seed_data.sql` (DML), all Flask routes (DML) |
| **Ch.7** — Complex queries, Views | `views.sql` (4 views), `queries/*.sql` (9+ complex queries with JOINs, subqueries, aggregations) |
| **Ch.8** — Relational Algebra | Views implement SELECT (σ), PROJECT (π), JOIN (⋈) operations |
| **Ch.14** — Normalization (2NF, 3NF, BCNF) | Users separated from students/faculty (2NF), no transitive deps (3NF) |
| **Ch.20** — Transaction processing, ACID | Stored procedures with COMMIT/ROLLBACK, error handling with rollback |
| **Ch.21** — Concurrency control | Connection pool in `db_connector.py`, MySQL InnoDB row-level locking |
| **Ch.22** — Recovery | MySQL InnoDB redo/undo logs, crash recovery |

---

## 📄 License

This project is developed for academic purposes as part of a Database Systems course.

---

> **Built with ❤️ by the Smart Campus Team**
