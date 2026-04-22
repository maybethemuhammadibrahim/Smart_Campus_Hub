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
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_username_len CHECK (LENGTH(username) >= 3)
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
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_student_email CHECK (email LIKE '%@%'),
    CONSTRAINT chk_student_cgpa CHECK (cgpa BETWEEN 0.00 AND 4.00)
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
        REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT chk_faculty_email CHECK (email LIKE '%@%')
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
        REFERENCES faculty(faculty_id) ON DELETE SET NULL,
    CONSTRAINT chk_credit_hours CHECK (credit_hours BETWEEN 1 AND 3),
    CONSTRAINT chk_max_capacity CHECK (max_capacity BETWEEN 1 AND 500)
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
    CONSTRAINT uq_attendance UNIQUE (enrollment_id, class_date),
    CONSTRAINT chk_class_date CHECK (class_date <= CURDATE())
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
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT chk_total_marks CHECK (total_marks > 0),
    CONSTRAINT chk_marks_obtained CHECK (marks_obtained BETWEEN 0 AND total_marks),
    CONSTRAINT chk_grade_points CHECK (grade_points BETWEEN 0.00 AND 4.00)
);

-- ============================================================
-- TABLE 8: audit_log
-- Tracks modifications to grades and attendance for accountability
-- Covers: Ch.20 Transaction Processing, data auditing
-- ============================================================
CREATE TABLE audit_log (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    table_name  VARCHAR(50)  NOT NULL,
    record_id   INT          NOT NULL,
    action      ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    changed_by  INT,
    changed_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PERFORMANCE INDEXES
-- Covers: Ch.21 Concurrency & performance optimization
-- ============================================================
CREATE INDEX idx_enrollments_student ON enrollments(student_id);
CREATE INDEX idx_enrollments_course  ON enrollments(course_id);
CREATE INDEX idx_enrollments_status  ON enrollments(status);
CREATE INDEX idx_attendance_date     ON attendance(class_date);
CREATE INDEX idx_grades_enrollment   ON grades(enrollment_id);
CREATE INDEX idx_courses_faculty     ON courses(faculty_id);
CREATE INDEX idx_audit_table_record  ON audit_log(table_name, record_id);