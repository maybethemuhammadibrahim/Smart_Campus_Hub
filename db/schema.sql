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
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,         -- bcrypt hash
    role          ENUM('student','faculty','admin') NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_username_len CHECK (LENGTH(username) >= 3)
);

-- ============================================================
-- TABLE 2: students
-- FK to users. Avoids storing auth + personal data together (BCNF)
-- cgpa is now computed via v_student_cgpa view (not stored)
-- ============================================================
CREATE TABLE IF NOT EXISTS students (
    student_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL UNIQUE,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    dob         DATE,
    program     VARCHAR(100),
    batch_year  YEAR,
    CONSTRAINT fk_student_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_student_email CHECK (email LIKE '%@%')
);

-- ============================================================
-- TABLE 3: faculty
-- ============================================================
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL UNIQUE,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    department  VARCHAR(100),
    designation VARCHAR(100),
    CONSTRAINT fk_faculty_user FOREIGN KEY (user_id)
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_faculty_email CHECK (email LIKE '%@%')
);

-- ============================================================
-- TABLE 4: courses  (catalog only — no offering-level data)
-- Removed: semester, faculty_id, max_capacity
-- ============================================================
CREATE TABLE IF NOT EXISTS courses (
    course_id    INT AUTO_INCREMENT PRIMARY KEY,
    course_code  VARCHAR(20)  NOT NULL UNIQUE,
    course_name  VARCHAR(150) NOT NULL,
    credit_hours TINYINT      NOT NULL DEFAULT 3,
    CONSTRAINT chk_credit_hours CHECK (credit_hours BETWEEN 1 AND 3)
);

-- ============================================================
-- TABLE 5: semesters
-- Represents an academic term/offering period
-- ============================================================
CREATE TABLE IF NOT EXISTS semesters (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,
    start_date  DATE         NOT NULL,
    end_date    DATE         NOT NULL,
    is_active   BOOLEAN      DEFAULT FALSE,
    CONSTRAINT chk_semester_dates CHECK (end_date > start_date)
);

-- ============================================================
-- TABLE 6: course_sections
-- Resolves the offering of a course in a semester by a faculty member
-- ============================================================
CREATE TABLE IF NOT EXISTS course_sections (
    section_id   INT AUTO_INCREMENT PRIMARY KEY,
    course_id    INT          NOT NULL,
    semester_id  INT          NOT NULL,
    faculty_id   INT,
    section_code VARCHAR(20)  NOT NULL,
    max_capacity SMALLINT     DEFAULT 40,
    CONSTRAINT fk_cs_course    FOREIGN KEY (course_id)
        REFERENCES courses(course_id)   ON DELETE CASCADE,
    CONSTRAINT fk_cs_semester  FOREIGN KEY (semester_id)
        REFERENCES semesters(semester_id) ON DELETE CASCADE,
    CONSTRAINT fk_cs_faculty   FOREIGN KEY (faculty_id)
        REFERENCES faculty(faculty_id)  ON DELETE SET NULL,
    CONSTRAINT uq_section      UNIQUE (course_id, semester_id, section_code),
    CONSTRAINT chk_cs_capacity CHECK (max_capacity BETWEEN 1 AND 500)
);

-- ============================================================
-- TABLE 7: enrollments
-- Junction table: resolves M:N between students and course_sections
-- ============================================================
CREATE TABLE IF NOT EXISTS enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id    INT NOT NULL,
    section_id    INT NOT NULL,
    enrolled_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    status        ENUM('active','dropped','completed') DEFAULT 'active',
    CONSTRAINT fk_enroll_student  FOREIGN KEY (student_id)
        REFERENCES students(student_id)       ON DELETE CASCADE,
    CONSTRAINT fk_enroll_section  FOREIGN KEY (section_id)
        REFERENCES course_sections(section_id) ON DELETE CASCADE,
    CONSTRAINT uq_enrollment UNIQUE (student_id, section_id)
);

-- ============================================================
-- TABLE 8: attendance
-- One enrollment → many attendance records
-- date + enrollment_id → functional dependency (BCNF satisfied)
-- marked_by FK enforces referential integrity to users
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT  NOT NULL,
    class_date    DATE NOT NULL,
    status        ENUM('present','absent','late') NOT NULL,
    marked_by     INT,                            -- FK → users(user_id)
    CONSTRAINT fk_attend_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT fk_attend_marked_by  FOREIGN KEY (marked_by)
        REFERENCES users(user_id)             ON DELETE SET NULL,
    CONSTRAINT uq_attendance UNIQUE (enrollment_id, class_date)
    -- No-future-date enforced via trg_attendance_before_insert / _before_update
);

-- ============================================================
-- TABLE 9: grades
-- One enrollment → one grade record (1:1 via enrollment)
-- Stores raw marks + computed letter grade
-- ============================================================
CREATE TABLE IF NOT EXISTS grades (
    grade_id       INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id  INT          NOT NULL UNIQUE,
    marks_obtained DECIMAL(5,2) DEFAULT 0,
    total_marks    DECIMAL(5,2) DEFAULT 100,
    letter_grade   CHAR(2),
    grade_points   DECIMAL(3,2),
    CONSTRAINT fk_grade_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT chk_total_marks   CHECK (total_marks > 0),
    CONSTRAINT chk_marks_obtained CHECK (marks_obtained BETWEEN 0 AND total_marks),
    CONSTRAINT chk_grade_points   CHECK (grade_points BETWEEN 0.00 AND 4.00)
);

-- ============================================================
-- TABLE 10: audit_log
-- Tracks modifications to grades and attendance for accountability
-- Covers: Ch.20 Transaction Processing, data auditing
-- changed_by FK enforces referential integrity to users
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    table_name  VARCHAR(50)  NOT NULL,
    record_id   INT          NOT NULL,
    action      ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    changed_by  INT,
    changed_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_changed_by FOREIGN KEY (changed_by)
        REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================================================
-- PERFORMANCE INDEXES
-- Covers: Ch.21 Concurrency & performance optimization
-- Note: idx_grades_enrollment removed — superseded by UNIQUE on enrollment_id
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_enrollments_student  ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_section  ON enrollments(section_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_status   ON enrollments(status);
CREATE INDEX IF NOT EXISTS idx_attendance_date      ON attendance(class_date);
CREATE INDEX IF NOT EXISTS idx_cs_course            ON course_sections(course_id);
CREATE INDEX IF NOT EXISTS idx_cs_semester          ON course_sections(semester_id);
CREATE INDEX IF NOT EXISTS idx_cs_faculty           ON course_sections(faculty_id);
CREATE INDEX IF NOT EXISTS idx_audit_table_record   ON audit_log(table_name, record_id);