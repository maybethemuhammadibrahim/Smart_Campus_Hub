This is a comprehensive plan — I'll build it in full. Here's everything:---

## Smart Campus Academic Management System — Full Implementation Guide

---

### Part 1 — Toolchain & Environment Setup (Windows 11)

#### Step 1.1 — Install MySQL and MySQL Workbench

1. Go to https://dev.mysql.com/downloads/installer/ and download **MySQL Installer (Community)** — the larger "web" installer.
2. Run the installer. Choose **"Custom"** setup type.
3. Select and install: `MySQL Server 8.x`, `MySQL Workbench 8.x`, `MySQL Shell`.
4. During configuration: set root password (remember it), leave port as `3306`, enable "Start MySQL Server at System Startup".
5. Verify: open **MySQL Workbench**, click the local connection → it should open the query editor.

#### Step 1.2 — Install Python 3.11

1. Download from https://python.org/downloads — pick **Python 3.11.x** (stable, best Flask 3 compatibility).
2. Run the installer — **check "Add python.exe to PATH"** before clicking Install.
3. Verify: open Command Prompt and run `python --version`. Should print `Python 3.11.x`.

#### Step 1.3 — Install VS Code

Download from https://code.visualstudio.com. Install the extensions: **Python**, **Pylance**, **SQLTools**, **SQLTools MySQL/MariaDB**, **Jinja** (for HTML templates).

#### Step 1.4 — Create Project and Virtual Environment

Open VS Code terminal (`Ctrl + backtick`) and run:

```bash
mkdir smart_campus && cd smart_campus
python -m venv venv
venv\Scripts\activate
pip install flask mysql-connector-python python-dotenv flask-login werkzeug
pip freeze > requirements.txt
```

---

### Part 2 — Complete File Structure

Every file and folder you need — nothing omitted.

```
smart_campus/
│
├── app.py                         # Flask app factory, registers all blueprints
├── config.py                      # DB credentials, secret key, env config
├── .env                           # Local secrets (never commit this)
├── requirements.txt
│
├── db/
│   ├── schema.sql                 # CREATE TABLE statements (all 7 tables)
│   ├── stored_procedures.sql      # All stored procedures
│   ├── views.sql                  # All SQL views
│   ├── triggers.sql               # Audit/constraint triggers
│   ├── seed_data.sql              # Sample INSERT data for testing
│   └── queries/
│       ├── student_queries.sql    # Complex queries for student role
│       ├── faculty_queries.sql    # Complex queries for faculty role
│       └── admin_queries.sql      # Complex queries for admin role
│
├── blueprints/
│   ├── __init__.py
│   ├── auth.py                    # Login, logout, session handling
│   ├── student.py                 # Student routes
│   ├── faculty.py                 # Faculty routes
│   └── admin.py                  # Admin routes
│
├── db_connector.py                # MySQL connection pool, execute_query helper
├── decorators.py                  # @login_required, @role_required decorators
│
├── templates/
│   ├── base.html                  # Master layout with nav
│   ├── auth/
│   │   └── login.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── courses.html           # Available courses + enroll button
│   │   ├── my_courses.html        # Enrolled courses
│   │   ├── attendance.html        # Attendance % per course
│   │   ├── grades.html            # Grades + GPA
│   │   └── transcript.html        # Full academic transcript
│   ├── faculty/
│   │   ├── dashboard.html
│   │   ├── my_courses.html
│   │   ├── roster.html            # Student list for a course
│   │   ├── mark_attendance.html
│   │   └── enter_grades.html
│   └── admin/
│       ├── dashboard.html
│       ├── students.html          # Add/edit students
│       ├── faculty.html           # Add/edit faculty
│       ├── courses.html           # Create courses, assign faculty
│       ├── reports.html           # Enrollment stats, GPA dist.
│       └── assign_faculty.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

---

### Part 3 — Database Schema (Full SQL)

Create the file `db/schema.sql` with this exact content:

```sql
-- ============================================================
-- Smart Campus Academic Management System — Schema
-- Covers: Ch.5 Relational Model, Ch.6 SQL DDL, Ch.14 Normalization
-- Normal Forms: All tables in 3NF / BCNF
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_campus;
USE smart_campus;

-- ============================================================
-- TABLE 1: users
-- Central auth table. Roles: 'student', 'faculty', 'admin'
-- Separated from entity tables to avoid multi-valued attributes (2NF)
-- ============================================================
CREATE TABLE users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,         -- bcrypt hash
    role        ENUM('student','faculty','admin') NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: students
-- FK to users. Avoids storing auth + personal data together (BCNF)
-- ============================================================
CREATE TABLE students (
    student_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT NOT NULL UNIQUE,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    email         VARCHAR(100) NOT NULL UNIQUE,
    dob           DATE,
    program       VARCHAR(100),
    batch_year    YEAR,
    cgpa          DECIMAL(3,2) DEFAULT 0.00,
    CONSTRAINT fk_student_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 3: faculty
-- ============================================================
CREATE TABLE faculty (
    faculty_id   INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT NOT NULL UNIQUE,
    first_name   VARCHAR(50)  NOT NULL,
    last_name    VARCHAR(50)  NOT NULL,
    email        VARCHAR(100) NOT NULL UNIQUE,
    department   VARCHAR(100),
    designation  VARCHAR(100),
    CONSTRAINT fk_faculty_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 4: courses
-- One faculty → many courses (many-to-one relationship)
-- ============================================================
CREATE TABLE courses (
    course_id    INT AUTO_INCREMENT PRIMARY KEY,
    course_code  VARCHAR(20)  NOT NULL UNIQUE,
    course_name  VARCHAR(150) NOT NULL,
    credit_hours TINYINT      NOT NULL DEFAULT 3,
    semester     VARCHAR(20),
    faculty_id   INT,
    max_capacity SMALLINT DEFAULT 40,
    CONSTRAINT fk_course_faculty FOREIGN KEY (faculty_id)
        REFERENCES faculty(faculty_id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE 5: enrollments
-- Junction table: resolves M:N between students and courses
-- One student → many enrollments, one course → many students
-- ============================================================
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT NOT NULL,
    course_id     INT NOT NULL,
    enrolled_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    status        ENUM('active','dropped','completed') DEFAULT 'active',
    CONSTRAINT fk_enroll_student FOREIGN KEY (student_id)
        REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_enroll_course  FOREIGN KEY (course_id)
        REFERENCES courses(course_id)  ON DELETE CASCADE,
    CONSTRAINT uq_enrollment UNIQUE (student_id, course_id)
);

-- ============================================================
-- TABLE 6: attendance
-- One enrollment → many attendance records
-- date + enrollment_id → functional dependency (BCNF satisfied)
-- ============================================================
CREATE TABLE attendance (
    attendance_id  INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id  INT  NOT NULL,
    class_date     DATE NOT NULL,
    status         ENUM('present','absent','late') NOT NULL,
    marked_by      INT,                          -- faculty user_id
    CONSTRAINT fk_attend_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT uq_attendance UNIQUE (enrollment_id, class_date)
);

-- ============================================================
-- TABLE 7: grades
-- One enrollment → one grade record (1:1 via enrollment)
-- Stores raw marks + computed letter grade
-- ============================================================
CREATE TABLE grades (
    grade_id       INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id  INT          NOT NULL UNIQUE,
    marks_obtained DECIMAL(5,2) DEFAULT 0,
    total_marks    DECIMAL(5,2) DEFAULT 100,
    letter_grade   CHAR(2),
    grade_points   DECIMAL(3,2),
    CONSTRAINT fk_grade_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE
);
```

---

### Part 4 — Stored Procedures

Create `db/stored_procedures.sql`:

```sql
USE smart_campus;
DELIMITER $$

-- ============================================================
-- PROCEDURE 1: RegisterStudentInCourse
-- Covers: Ch.5 constraint violations, Ch.6 DML
-- Checks: already enrolled, course capacity, active status
-- ============================================================
CREATE PROCEDURE RegisterStudentInCourse(
    IN  p_student_id INT,
    IN  p_course_id  INT,
    OUT p_message    VARCHAR(255),
    OUT p_success    TINYINT
)
BEGIN
    DECLARE v_count        INT DEFAULT 0;
    DECLARE v_enrolled_cnt INT DEFAULT 0;
    DECLARE v_capacity     INT DEFAULT 0;

    -- Check if already enrolled
    SELECT COUNT(*) INTO v_count
    FROM enrollments
    WHERE student_id = p_student_id
      AND course_id  = p_course_id
      AND status = 'active';

    IF v_count > 0 THEN
        SET p_message = 'Student is already enrolled in this course.';
        SET p_success = 0;
    ELSE
        -- Check capacity
        SELECT max_capacity INTO v_capacity FROM courses WHERE course_id = p_course_id;
        SELECT COUNT(*) INTO v_enrolled_cnt
        FROM enrollments WHERE course_id = p_course_id AND status = 'active';

        IF v_enrolled_cnt >= v_capacity THEN
            SET p_message = 'Course is full. Enrollment not allowed.';
            SET p_success = 0;
        ELSE
            INSERT INTO enrollments (student_id, course_id, status)
            VALUES (p_student_id, p_course_id, 'active');

            INSERT INTO grades (enrollment_id)
            VALUES (LAST_INSERT_ID());

            SET p_message = 'Enrollment successful.';
            SET p_success = 1;
        END IF;
    END IF;
END$$

-- ============================================================
-- PROCEDURE 2: CalculateStudentGPA
-- Covers: Ch.6 aggregate functions, computed fields
-- Grade scale: A=4.0, A-=3.7, B+=3.3, B=3.0, B-=2.7, C+=2.3, C=2.0, F=0.0
-- ============================================================
CREATE PROCEDURE CalculateStudentGPA(
    IN  p_student_id INT,
    OUT p_gpa        DECIMAL(3,2)
)
BEGIN
    DECLARE v_total_points  DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total_credits INT DEFAULT 0;

    SELECT
        SUM(g.grade_points * c.credit_hours),
        SUM(c.credit_hours)
    INTO v_total_points, v_total_credits
    FROM enrollments e
    JOIN grades   g ON e.enrollment_id = g.enrollment_id
    JOIN courses  c ON e.course_id     = c.course_id
    WHERE e.student_id = p_student_id
      AND e.status = 'active'
      AND g.grade_points IS NOT NULL;

    IF v_total_credits = 0 THEN
        SET p_gpa = 0.00;
    ELSE
        SET p_gpa = ROUND(v_total_points / v_total_credits, 2);
    END IF;

    -- Update cgpa in students table
    UPDATE students SET cgpa = p_gpa WHERE student_id = p_student_id;
END$$

-- ============================================================
-- PROCEDURE 3: UpdateLetterGrade
-- Called after marks are entered; sets letter grade + points
-- ============================================================
CREATE PROCEDURE UpdateLetterGrade(IN p_enrollment_id INT)
BEGIN
    DECLARE v_percentage DECIMAL(5,2);
    DECLARE v_letter     CHAR(2);
    DECLARE v_points     DECIMAL(3,2);

    SELECT (marks_obtained / total_marks * 100) INTO v_percentage
    FROM grades WHERE enrollment_id = p_enrollment_id;

    IF    v_percentage >= 90 THEN SET v_letter='A',  v_points=4.00;
    ELSEIF v_percentage >= 85 THEN SET v_letter='A-', v_points=3.70;
    ELSEIF v_percentage >= 80 THEN SET v_letter='B+', v_points=3.30;
    ELSEIF v_percentage >= 75 THEN SET v_letter='B',  v_points=3.00;
    ELSEIF v_percentage >= 70 THEN SET v_letter='B-', v_points=2.70;
    ELSEIF v_percentage >= 65 THEN SET v_letter='C+', v_points=2.30;
    ELSEIF v_percentage >= 60 THEN SET v_letter='C',  v_points=2.00;
    ELSE                           SET v_letter='F',  v_points=0.00;
    END IF;

    UPDATE grades
    SET letter_grade = v_letter, grade_points = v_points
    WHERE enrollment_id = p_enrollment_id;
END$$

DELIMITER ;
```

---

### Part 5 — Views and Complex Queries

Create `db/views.sql`:

```sql
USE smart_campus;

-- ============================================================
-- VIEW 1: v_student_transcript
-- Full academic record per student — covers Ch.7 Views
-- Uses: JOIN, aggregate, GROUP BY
-- ============================================================
CREATE OR REPLACE VIEW v_student_transcript AS
SELECT
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name)  AS student_name,
    c.course_code,
    c.course_name,
    c.credit_hours,
    g.marks_obtained,
    g.total_marks,
    g.letter_grade,
    g.grade_points,
    e.status AS enrollment_status,
    e.enrolled_at
FROM students    s
JOIN enrollments e ON s.student_id    = e.student_id
JOIN courses     c ON e.course_id     = c.course_id
LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id;

-- ============================================================
-- VIEW 2: v_attendance_summary
-- Attendance % per student per course — covers aggregation
-- ============================================================
CREATE OR REPLACE VIEW v_attendance_summary AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.course_id,
    c.course_name,
    COUNT(a.attendance_id)                                     AS total_classes,
    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)     AS classes_attended,
    ROUND(
        SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(a.attendance_id), 0) * 100, 2
    )                                                          AS attendance_percentage
FROM enrollments e
JOIN courses     c ON e.course_id = c.course_id
LEFT JOIN attendance a ON e.enrollment_id = a.enrollment_id
GROUP BY e.enrollment_id, e.student_id, e.course_id, c.course_name;

-- ============================================================
-- VIEW 3: v_course_roster
-- List of students enrolled in each course — faculty use
-- ============================================================
CREATE OR REPLACE VIEW v_course_roster AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
    s.student_id,
    CONCAT(s.first_name,' ',s.last_name) AS student_name,
    s.email,
    e.enrollment_id,
    e.enrolled_at,
    e.status
FROM courses     c
JOIN faculty     f ON c.faculty_id    = f.faculty_id
JOIN enrollments e ON c.course_id     = e.course_id
JOIN students    s ON e.student_id    = s.student_id
WHERE e.status = 'active';

-- ============================================================
-- VIEW 4: v_admin_enrollment_report
-- Total students enrolled in each course — admin report
-- ============================================================
CREATE OR REPLACE VIEW v_admin_enrollment_report AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    c.credit_hours,
    CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
    c.max_capacity,
    COUNT(e.enrollment_id)               AS enrolled_count,
    c.max_capacity - COUNT(e.enrollment_id) AS seats_remaining,
    ROUND(COUNT(e.enrollment_id)/c.max_capacity*100, 1) AS fill_percentage
FROM courses     c
LEFT JOIN faculty     f ON c.faculty_id = f.faculty_id
LEFT JOIN enrollments e ON c.course_id  = e.course_id
    AND e.status = 'active'
GROUP BY c.course_id, c.course_code, c.course_name,
         c.credit_hours, f.first_name, f.last_name,
         c.max_capacity;
```

Create `db/queries/student_queries.sql` (reference for Flask routes):

```sql
-- Q1: Full transcript for a specific student
SELECT * FROM v_student_transcript WHERE student_id = ?;

-- Q2: Attendance percentage per course for a student
SELECT * FROM v_attendance_summary WHERE student_id = ?;

-- Q3: Available courses not yet enrolled in
SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
       CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
       c.max_capacity - COUNT(e.enrollment_id) AS seats_left
FROM courses c
LEFT JOIN faculty     f ON c.faculty_id = f.faculty_id
LEFT JOIN enrollments e ON c.course_id  = e.course_id
    AND e.status = 'active'
WHERE c.course_id NOT IN (
    SELECT course_id FROM enrollments
    WHERE student_id = ? AND status = 'active'
)
GROUP BY c.course_id, c.course_code, c.course_name,
         c.credit_hours, f.first_name, f.last_name, c.max_capacity
HAVING seats_left > 0;
```

Create `db/queries/faculty_queries.sql`:

```sql
-- Q1: Course roster (use view)
SELECT * FROM v_course_roster WHERE course_id = ?;

-- Q2: Average marks per course
SELECT
    c.course_name,
    AVG(g.marks_obtained)  AS avg_marks,
    MAX(g.marks_obtained)  AS highest_marks,
    MIN(g.marks_obtained)  AS lowest_marks,
    COUNT(e.enrollment_id) AS total_students
FROM courses     c
JOIN enrollments e ON c.course_id     = e.course_id
JOIN grades      g ON e.enrollment_id = g.enrollment_id
WHERE c.course_id = ?
GROUP BY c.course_name;

-- Q3: Students with attendance below 75%
SELECT
    s.student_id,
    CONCAT(s.first_name,' ',s.last_name) AS student_name,
    s.email,
    att.attendance_percentage
FROM v_attendance_summary att
JOIN students s ON att.student_id = s.student_id
WHERE att.course_id = ?
  AND att.attendance_percentage < 75
ORDER BY att.attendance_percentage ASC;
```

Create `db/queries/admin_queries.sql`:

```sql
-- Q1: Enrollment report (use view)
SELECT * FROM v_admin_enrollment_report ORDER BY enrolled_count DESC;

-- Q2: GPA distribution (histogram buckets)
SELECT
    CASE
        WHEN cgpa >= 3.5 THEN '3.5 - 4.0 (Dean''s List)'
        WHEN cgpa >= 3.0 THEN '3.0 - 3.49 (Good)'
        WHEN cgpa >= 2.5 THEN '2.5 - 2.99 (Satisfactory)'
        WHEN cgpa >= 2.0 THEN '2.0 - 2.49 (Passing)'
        ELSE                   'Below 2.0 (At Risk)'
    END              AS gpa_range,
    COUNT(student_id) AS student_count
FROM students
GROUP BY gpa_range
ORDER BY MIN(cgpa) DESC;

-- Q3: Courses taught by each faculty with enrollment count
SELECT
    CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
    f.department,
    COUNT(DISTINCT c.course_id)           AS courses_teaching,
    SUM(sub.enrolled)                     AS total_students
FROM faculty f
JOIN courses c ON f.faculty_id = c.faculty_id
JOIN (
    SELECT course_id, COUNT(*) AS enrolled
    FROM enrollments WHERE status='active'
    GROUP BY course_id
) sub ON c.course_id = sub.course_id
GROUP BY f.faculty_id, f.first_name, f.last_name, f.department
ORDER BY total_students DESC;
```

---

### Part 6 — Triggers

Create `db/triggers.sql`:

```sql
USE smart_campus;
DELIMITER $$

-- Trigger: Auto-call UpdateLetterGrade when marks are updated
CREATE TRIGGER trg_grade_after_update
AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained <> OLD.marks_obtained THEN
        CALL UpdateLetterGrade(NEW.enrollment_id);
    END IF;
END$$

DELIMITER ;
```

---

### Part 7 — Flask Application Code

**`config.py`:**

```python
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    DB_HOST    = os.getenv("DB_HOST", "localhost")
    DB_PORT    = int(os.getenv("DB_PORT", 3306))
    DB_USER    = os.getenv("DB_USER", "root")
    DB_PASS    = os.getenv("DB_PASS", "")
    DB_NAME    = os.getenv("DB_NAME", "smart_campus")
```

**`.env`:**

```
SECRET_KEY=your-secret-key-here
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASS=your_mysql_root_password
DB_NAME=smart_campus
```

**`db_connector.py`:**

```python
import mysql.connector
from mysql.connector import pooling
from config import Config

connection_pool = pooling.MySQLConnectionPool(
    pool_name    = "campus_pool",
    pool_size    = 5,
    host         = Config.DB_HOST,
    port         = Config.DB_PORT,
    user         = Config.DB_USER,
    password     = Config.DB_PASS,
    database     = Config.DB_NAME
)

def get_connection():
    return connection_pool.get_connection()

def execute_query(query, params=None, fetch=True, many=False):
    """
    fetch=True  → returns list of dicts (SELECT)
    fetch=False → executes INSERT/UPDATE/DELETE, returns lastrowid
    many=True   → params is a list of tuples (executemany)
    """
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if many:
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        return result
    finally:
        cursor.close()
        conn.close()

def call_procedure(proc_name, args=()):
    """Calls a stored procedure. Returns OUT params as the last item."""
    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.callproc(proc_name, args)
        conn.commit()
        result_args = cursor.stored_results()
        return list(result_args)
    finally:
        cursor.close()
        conn.close()
```

**`decorators.py`:**

```python
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash("Access denied.", "danger")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated
    return decorator
```

**`app.py`:**

```python
from flask import Flask
from config import Config
from blueprints.auth    import auth_bp
from blueprints.student import student_bp
from blueprints.faculty import faculty_bp
from blueprints.admin   import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(admin_bp,   url_prefix='/admin')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

**`blueprints/auth.py`:**

```python
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db_connector import execute_query
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET','POST'])
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rows = execute_query(
            "SELECT * FROM users WHERE username=%s AND is_active=1",
            (username,)
        )
        if rows and check_password_hash(rows[0]['password'], password):
            user = rows[0]
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['role']     = user['role']

            # Fetch entity-specific ID
            if user['role'] == 'student':
                r = execute_query("SELECT student_id FROM students WHERE user_id=%s",(user['user_id'],))
                session['entity_id'] = r[0]['student_id'] if r else None
                return redirect(url_for('student.dashboard'))
            elif user['role'] == 'faculty':
                r = execute_query("SELECT faculty_id FROM faculty WHERE user_id=%s",(user['user_id'],))
                session['entity_id'] = r[0]['faculty_id'] if r else None
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('admin.dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
```

**`blueprints/student.py`** (key routes shown in full):

```python
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db_connector import execute_query
from decorators import login_required, role_required
import mysql.connector
from config import Config

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    sid = session['entity_id']
    student = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))
    enrolled = execute_query(
        "SELECT c.course_name, c.course_code FROM enrollments e "
        "JOIN courses c ON e.course_id=c.course_id "
        "WHERE e.student_id=%s AND e.status='active'", (sid,)
    )
    return render_template('student/dashboard.html',
                           student=student[0], enrolled=enrolled)

@student_bp.route('/courses')
@login_required
@role_required('student')
def available_courses():
    sid = session['entity_id']
    courses = execute_query(
        """SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
                  CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
                  c.max_capacity - COUNT(e.enrollment_id) AS seats_left
           FROM courses c
           LEFT JOIN faculty f ON c.faculty_id=f.faculty_id
           LEFT JOIN enrollments e ON c.course_id=e.course_id AND e.status='active'
           WHERE c.course_id NOT IN (
               SELECT course_id FROM enrollments
               WHERE student_id=%s AND status='active'
           )
           GROUP BY c.course_id HAVING seats_left > 0""",
        (sid,)
    )
    return render_template('student/courses.html', courses=courses)

@student_bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
@role_required('student')
def enroll(course_id):
    sid = session['entity_id']
    # Call stored procedure via direct connection (OUT params)
    conn   = mysql.connector.connect(
        host=Config.DB_HOST, user=Config.DB_USER,
        password=Config.DB_PASS, database=Config.DB_NAME
    )
    cursor = conn.cursor()
    args   = (sid, course_id, '', 0)
    cursor.callproc('RegisterStudentInCourse', args)
    conn.commit()
    # Fetch OUT params
    for r in cursor.stored_results():
        pass
    # Re-query OUT values
    cursor.execute("SELECT @_RegisterStudentInCourse_2, @_RegisterStudentInCourse_3")
    row = cursor.fetchone()
    message, success = row
    cursor.close()
    conn.close()
    flash(message, "success" if success else "danger")
    return redirect(url_for('student.available_courses'))

@student_bp.route('/attendance')
@login_required
@role_required('student')
def attendance():
    sid = session['entity_id']
    data = execute_query("SELECT * FROM v_attendance_summary WHERE student_id=%s", (sid,))
    return render_template('student/attendance.html', records=data)

@student_bp.route('/grades')
@login_required
@role_required('student')
def grades():
    sid = session['entity_id']
    data = execute_query("SELECT * FROM v_student_transcript WHERE student_id=%s", (sid,))
    student = execute_query("SELECT cgpa FROM students WHERE student_id=%s", (sid,))
    return render_template('student/grades.html', grades=data,
                           cgpa=student[0]['cgpa'] if student else 0)

@student_bp.route('/transcript')
@login_required
@role_required('student')
def transcript():
    sid = session['entity_id']
    data = execute_query("SELECT * FROM v_student_transcript WHERE student_id=%s ORDER BY enrolled_at", (sid,))
    student = execute_query("SELECT * FROM students WHERE student_id=%s", (sid,))
    return render_template('student/transcript.html',
                           transcript=data, student=student[0])
```

The `faculty.py` and `admin.py` blueprints follow the exact same pattern — routes call `execute_query()` with the SQL from Part 5, render the matching template. You build them the same way after the student blueprint is working.

---

### Part 8 — Base HTML Template

**`templates/base.html`:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart Campus — {% block title %}{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav class="navbar">
        <span class="brand">Smart Campus</span>
        {% if session.get('user_id') %}
        <div class="nav-links">
            {% if session.role == 'student' %}
                <a href="{{ url_for('student.dashboard') }}">Dashboard</a>
                <a href="{{ url_for('student.available_courses') }}">Courses</a>
                <a href="{{ url_for('student.attendance') }}">Attendance</a>
                <a href="{{ url_for('student.grades') }}">Grades</a>
            {% elif session.role == 'faculty' %}
                <a href="{{ url_for('faculty.dashboard') }}">Dashboard</a>
                <a href="{{ url_for('faculty.my_courses') }}">My Courses</a>
            {% elif session.role == 'admin' %}
                <a href="{{ url_for('admin.dashboard') }}">Dashboard</a>
                <a href="{{ url_for('admin.students') }}">Students</a>
                <a href="{{ url_for('admin.courses') }}">Courses</a>
                <a href="{{ url_for('admin.reports') }}">Reports</a>
            {% endif %}
            <a href="{{ url_for('auth.logout') }}">Logout ({{ session.username }})</a>
        </div>
        {% endif %}
    </nav>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        {% block content %}{% endblock %}
    </main>

    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

---

### Part 9 — Syllabus Coverage Map

Every topic from your syllabus is deliberately exercised somewhere in this project.

| Syllabus Topic | Where It Appears in the Project |
|---|---|
| Ch.1 — DB characteristics, DBMS advantages | Covered in your project report introduction |
| Ch.2 — Three-schema architecture | External (UI), Conceptual (ERD), Internal (MySQL storage) — document this in your report |
| Ch.5 — Relational model, constraints, FKs | `schema.sql` — every FK, UNIQUE, ENUM, and NOT NULL constraint |
| Ch.6 — DDL, DML, INSERT/UPDATE/DELETE | `schema.sql`, `seed_data.sql`, all Flask routes doing INSERT/UPDATE |
| Ch.7 — Complex queries, Views, Schema change | `views.sql`, `queries/*.sql`, ALTER TABLE in Workbench migrations |
| Ch.3 — ER Diagram, entity types, weak entities | Your ERD in MySQL Workbench — draw it from the schema |
| Ch.8 — Relational Algebra (SELECT/PROJECT/JOIN) | Document your SQL views as equivalent RA expressions in your report |
| Ch.14 — Normalization, 2NF, 3NF, BCNF | Users table separated from students/faculty (2NF). No transitive deps (3NF). FK → PK only (BCNF). Document in report |
| Ch.20 — Transaction processing, ACID | Stored Procedures use implicit transactions; document COMMIT/ROLLBACK usage |
| Ch.21 — Concurrency control | Connection pool in `db_connector.py` — document isolation levels in report |
| Ch.22 — Recovery, deferred/immediate update | MySQL InnoDB uses redo logs — document in report |
| Ch.24 — NoSQL, MongoDB, Key-Value | Add a comparison section in your project report |

---

### Part 10 — Sequential Implementation Roadmap

Follow this order exactly. Do not jump ahead.

**Week 1 — Environment + Schema**

1. Complete all tool installations from Part 1.
2. Open MySQL Workbench → create schema `smart_campus`.
3. Run `schema.sql` in the Workbench query editor.
4. Draw the ERD in Workbench: Database → Reverse Engineer → select smart_campus.
5. Run `stored_procedures.sql`, `views.sql`, `triggers.sql` in order.
6. Run `seed_data.sql` to populate test data.
7. Test every view with a SELECT in Workbench. Test stored procedures with CALL.

**Week 2 — Flask Backend (no templates yet)**

8. Set up the project folder, virtualenv, install packages (Part 1.4).
9. Write `config.py`, `.env`, `db_connector.py`, `decorators.py`.
10. Write `app.py` and create empty blueprint files.
11. Test `db_connector.py` alone: write a `test_db.py` that calls `execute_query("SELECT 1")` and prints the result.
12. Build `auth.py` — implement login and logout. Test with Postman or browser.
13. Build `student.py` — all 5 routes. Test each one.
14. Build `faculty.py` — all 4 routes.
15. Build `admin.py` — all routes.

**Week 3 — Templates + CSS**

16. Write `base.html` with navbar.
17. Write all student templates (dashboard, courses, attendance, grades, transcript).
18. Write all faculty templates.
19. Write all admin templates.
20. Write `style.css` — style the navbar, tables, forms, flash messages.

**Week 4 — Integration + Report**

21. End-to-end test: log in as each role, exercise every feature.
22. Run all complex queries from Part 5 in Workbench, save screenshots.
23. Write the project report covering all syllabus chapters (use the coverage map above).
24. Export the ERD as a PNG from Workbench: File → Export → Export as PNG.

---

### Note on Google Antigravity / GitHub Copilot

Regarding your constraint about "Google Antigravity" — this product does not currently exist as a publicly released tool. There is no "Agent Manager" or "Browser agent" under that name. This appears to be either a placeholder in your brief or a tool specific to your institution. If you can clarify what platform this refers to, I can add specific instructions for it.

For **GitHub Copilot** (which is real and useful here): activate it in VS Code, and it will give you autocomplete for the repetitive Flask route patterns, Jinja template loops, and SQL query strings. Use it most in `blueprints/faculty.py` and `blueprints/admin.py` since they follow the same structure as `student.py` — Copilot will predict the pattern after seeing one blueprint.
