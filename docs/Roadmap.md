## Smart Campus Academic Management System — Full Implementation Guide

---

### Part 1 — Toolchain & Environment Setup (Windows 11)

#### Step 1.1 — Install MySQL and MySQL Workbench

1. Go to [https://dev.mysql.com/downloads/installer/](https://dev.mysql.com/downloads/installer/) and download **MySQL Installer (Community)** — the larger "web" installer.
2. Run the installer. Choose **"Custom"** setup type.
3. Select and install: `MySQL Server 8.x`, `MySQL Workbench 8.x`, `MySQL Shell`.
4. During configuration: set root password (remember it), leave port as `3306`, enable "Start MySQL Server at System Startup".

#### Step 1.2 — Install Python 3.11

1. Download from [https://python.org/downloads](https://python.org/downloads) — pick **Python 3.11.x** (stable, best Flask 3 compatibility).
2. Run the installer — **check "Add python.exe to PATH"** before clicking Install.
3. Verify: open Command Prompt and run `python --version`. Should print `Python 3.11.x`.

#### Step 1.4 — Create Project and Virtual Environment

Open VS Code terminal (`Ctrl + backtick`) and run:

```bash
python -m venv venv
venv\Scripts\activate
pip install flask mysql-connector-python python-dotenv flask-login werkzeug
pip freeze > requirements.txt
```

#### Step 1.5 — Connecting to Local Server in MySQL Workbench

**Method 1: Using the Default Connection**
1. Open MySQL Workbench.
2. Locate the **MySQL Connections** section on the home screen.
3. Click the rectangular tile named **Local instance MySQL80** (or similar).
4. Enter the root password you set during installation when prompted.
5. Check **Save password in vault** to bypass this prompt in the future.
6. Click **OK**. The query editor window will open.

**Method 2: Creating a New Connection (If tile is missing)**
1. Open MySQL Workbench.
2. Click the **+** (plus) icon next to the **MySQL Connections** heading on the home screen.
3. A **Setup New Connection** dialog box will open.
4. Input the following parameters:
    * **Connection Name:** Local
    * **Connection Method:** Standard (TCP/IP)
    * **Hostname:** 127.0.0.1
    * **Port:** 3306
    * **Username:** root
5. Click **Test Connection** at the bottom right.
6. Enter your root password when prompted and click **OK**.
7. If the test succeeds, click **OK** to close the setup dialog.
8. Click the newly created **Local** tile on the home screen to open the query editor.

#### Step 1.6 — Executing SQL Scripts in MySQL Workbench

1. Click **File** in the top menu bar.
2. Select **Open SQL Script...** (or press `Ctrl+Shift+O`).
3. In the file explorer window that appears, navigate to your project directory and open the `db/` folder.
4. Select the file and click **Open**. The SQL code will load into a new query tab.
5. Click the **Execute** button (the yellow lightning bolt icon) located in the toolbar directly above the SQL code, or use the top menu: **Query > Execute (All or Selection)**.
6. Verify the execution in the **Output** panel at the bottom of the screen. You should see green checkmarks indicating the queries ran successfully.
7. Close the tab.
8. Repeat steps 1 through 7 for the files in this exact order:
    * `schema.sql`
    * `stored_procedures.sql`
    * `views.sql`
    * `triggers.sql`
    * `seed_data.sql`

#### Step 1.7 — Environment Configuration

1. In the root directory of the project, create a new file named `.env`.
2. Open the `.env` file and define your database credentials to allow `config.py` to read them.
3. Add the following lines, replacing `your_password` with the root password set during the MySQL installation:
   ```ini
   DB_HOST=127.0.0.1
   DB_USER=root
   DB_PASSWORD=your_password
   DB_NAME=smart_campus
   ```

---

### Part 2 — Complete File Structure

```text
smart_campus/
│
├── app.py                 # Flask app factory, registers all blueprints
├── config.py              # DB credentials, secret key, env config
├── .env                   # Local secrets (never commit this)
├── requirements.txt
│
├── db/
│   ├── schema.sql         # CREATE TABLE statements (all 7 tables)
│   ├── stored_procedures.sql # All stored procedures
│   ├── views.sql          # All SQL views
│   ├── triggers.sql       # Audit/constraint triggers
│   ├── seed_data.sql      # Sample INSERT data for testing
│   └── queries/
│       ├── student_queries.sql   # Complex queries for student role
│       ├── faculty_queries.sql   # Complex queries for faculty role
│       └── admin_queries.sql     # Complex queries for admin role
│
├── blueprints/
│   ├── __init__.py
│   ├── auth.py            # Login, logout, session handling
│   ├── student.py         # Student routes
│   ├── faculty.py         # Faculty routes
│   └── admin.py           # Admin routes
│
├── db_connector.py        # MySQL connection pool, execute_query helper
├── decorators.py          # @login_required, @role_required decorators
│
├── templates/
│   ├── base.html          # Master layout with nav
│   ├── auth/
│   │   └── login.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── courses.html   # Available courses + enroll button
│   │   ├── my_courses.html# Enrolled courses
│   │   ├── attendance.html# Attendance % per course
│   │   ├── grades.html    # Grades + GPA
│   │   └── transcript.html# Full academic transcript
│   ├── faculty/
│   │   ├── dashboard.html
│   │   ├── my_courses.html
│   │   ├── roster.html    # Student list for a course
│   │   ├── mark_attendance.html
│   │   └── enter_grades.html
│   └── admin/
│       ├── dashboard.html
│       ├── students.html  # Add/edit students
│       ├── faculty.html   # Add/edit faculty
│       ├── courses.html   # Create courses, assign faculty
│       ├── reports.html   # Enrollment stats, GPA dist.
│       └── assign_faculty.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

---

### Part 9 — Syllabus Coverage Map

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

**Week 1 — Environment + Schema**

1. Complete tool installations (Steps 1.1 - 1.4).
2. Connect to local server via MySQL Workbench (Step 1.5).
3. Open MySQL Workbench → create schema `smart_campus`.
4. Execute SQL scripts via Workbench in the exact order specified (Step 1.6).
5. Draw the ERD in Workbench: Database → Reverse Engineer → select smart_campus.
6. Test every view with a SELECT in Workbench. Test stored procedures with CALL.

**Week 2 — Flask Backend (no templates yet)**

7. Write `config.py`, `.env` (Step 1.7), `db_connector.py`, `decorators.py`.
8. Write `app.py` and create empty blueprint files.
9. Test `db_connector.py` alone: write a `test_db.py` that calls `execute_query("SELECT 1")` and prints the result.
10. Build `auth.py` — implement login and logout. Test with Postman or browser.
11. Build `student.py` — all 5 routes. Test each one.
12. Build `faculty.py` — all 4 routes.
13. Build `admin.py` — all routes.

**Week 3 — Templates + CSS**

14. Write `base.html` with navbar.
15. Write all student templates (dashboard, courses, attendance, grades, transcript).
16. Write all faculty templates.
17. Write all admin templates.
18. Write `style.css` — style the navbar, tables, forms, flash messages.

**Week 4 — Integration + Report**

19. End-to-end test: log in as each role, exercise every feature.
20. Run all complex queries in Workbench, save screenshots.
21. Write the project report covering all syllabus chapters (use the coverage map).
22. Export the ERD as a PNG from Workbench: File → Export → Export as PNG.

---
