-- database schema

CREATE DATABASE IF NOT EXISTS smart_campus;
USE smart_campus;

-- users table
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,         -- password hash
    role          ENUM('student','faculty','admin') NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_username_len CHECK (LENGTH(username) >= 3)
);

-- students table
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

-- faculty table
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

-- courses table
CREATE TABLE IF NOT EXISTS courses (
    course_id    INT AUTO_INCREMENT PRIMARY KEY,
    course_code  VARCHAR(20)  NOT NULL UNIQUE,
    course_name  VARCHAR(150) NOT NULL,
    credit_hours TINYINT      NOT NULL DEFAULT 3,
    CONSTRAINT chk_credit_hours CHECK (credit_hours BETWEEN 1 AND 3)
);

-- semesters table
CREATE TABLE IF NOT EXISTS semesters (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50)  NOT NULL UNIQUE,
    start_date  DATE         NOT NULL,
    end_date    DATE         NOT NULL,
    is_active   BOOLEAN      DEFAULT FALSE,
    CONSTRAINT chk_semester_dates CHECK (end_date > start_date)
);

-- course sections table
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

-- enrollments table
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

-- attendance table
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    enrollment_id INT  NOT NULL,
    class_date    DATE NOT NULL,
    status        ENUM('present','absent','late') NOT NULL,
    marked_by     INT,                            -- marked by user
    CONSTRAINT fk_attend_enrollment FOREIGN KEY (enrollment_id)
        REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
    CONSTRAINT fk_attend_marked_by  FOREIGN KEY (marked_by)
        REFERENCES users(user_id)             ON DELETE SET NULL,
    CONSTRAINT uq_attendance UNIQUE (enrollment_id, class_date)
);

-- grades table
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

-- audit log table
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

