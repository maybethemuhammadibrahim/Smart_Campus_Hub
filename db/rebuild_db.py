"""Rebuild the database from scratch using the new normalized schema."""
import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='1234')
cursor = conn.cursor()

cursor.execute("DROP DATABASE IF EXISTS smart_campus")
cursor.execute("CREATE DATABASE smart_campus")
cursor.execute("USE smart_campus")
conn.commit()
print("✅ Database recreated")

# ── Schema (without IF NOT EXISTS on indexes) ──
schema_stmts = [
    # users
    """CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL, role ENUM('student','faculty','admin') NOT NULL,
        is_active BOOLEAN DEFAULT TRUE, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT chk_username_len CHECK (LENGTH(username) >= 3))""",
    # students
    """CREATE TABLE students (
        student_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL UNIQUE,
        first_name VARCHAR(50) NOT NULL, last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE, dob DATE, program VARCHAR(100), batch_year YEAR,
        CONSTRAINT fk_student_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        CONSTRAINT chk_student_email CHECK (email LIKE '%@%'))""",
    # faculty
    """CREATE TABLE faculty (
        faculty_id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL UNIQUE,
        first_name VARCHAR(50) NOT NULL, last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE, department VARCHAR(100), designation VARCHAR(100),
        CONSTRAINT fk_faculty_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        CONSTRAINT chk_faculty_email CHECK (email LIKE '%@%'))""",
    # courses (catalog only)
    """CREATE TABLE courses (
        course_id INT AUTO_INCREMENT PRIMARY KEY, course_code VARCHAR(20) NOT NULL UNIQUE,
        course_name VARCHAR(150) NOT NULL, credit_hours TINYINT NOT NULL DEFAULT 3,
        CONSTRAINT chk_credit_hours CHECK (credit_hours BETWEEN 1 AND 3))""",
    # semesters
    """CREATE TABLE semesters (
        semester_id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50) NOT NULL UNIQUE,
        start_date DATE NOT NULL, end_date DATE NOT NULL, is_active BOOLEAN DEFAULT FALSE,
        CONSTRAINT chk_semester_dates CHECK (end_date > start_date))""",
    # course_sections
    """CREATE TABLE course_sections (
        section_id INT AUTO_INCREMENT PRIMARY KEY, course_id INT NOT NULL,
        semester_id INT NOT NULL, faculty_id INT, section_code VARCHAR(20) NOT NULL,
        max_capacity SMALLINT DEFAULT 40,
        CONSTRAINT fk_cs_course FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        CONSTRAINT fk_cs_semester FOREIGN KEY (semester_id) REFERENCES semesters(semester_id) ON DELETE CASCADE,
        CONSTRAINT fk_cs_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE SET NULL,
        CONSTRAINT uq_section UNIQUE (course_id, semester_id, section_code),
        CONSTRAINT chk_cs_capacity CHECK (max_capacity BETWEEN 1 AND 500))""",
    # enrollments
    """CREATE TABLE enrollments (
        enrollment_id INT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL,
        section_id INT NOT NULL, enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status ENUM('active','dropped','completed') DEFAULT 'active',
        CONSTRAINT fk_enroll_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        CONSTRAINT fk_enroll_section FOREIGN KEY (section_id) REFERENCES course_sections(section_id) ON DELETE CASCADE,
        CONSTRAINT uq_enrollment UNIQUE (student_id, section_id))""",
    # attendance
    """CREATE TABLE attendance (
        attendance_id INT AUTO_INCREMENT PRIMARY KEY, enrollment_id INT NOT NULL,
        class_date DATE NOT NULL, status ENUM('present','absent','late') NOT NULL, marked_by INT,
        CONSTRAINT fk_attend_enrollment FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
        CONSTRAINT fk_attend_marked_by FOREIGN KEY (marked_by) REFERENCES users(user_id) ON DELETE SET NULL,
        CONSTRAINT uq_attendance UNIQUE (enrollment_id, class_date))""",
    # grades
    """CREATE TABLE grades (
        grade_id INT AUTO_INCREMENT PRIMARY KEY, enrollment_id INT NOT NULL UNIQUE,
        marks_obtained DECIMAL(5,2) DEFAULT 0, total_marks DECIMAL(5,2) DEFAULT 100,
        letter_grade CHAR(2), grade_points DECIMAL(3,2),
        CONSTRAINT fk_grade_enrollment FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE,
        CONSTRAINT chk_total_marks CHECK (total_marks > 0),
        CONSTRAINT chk_marks_obtained CHECK (marks_obtained BETWEEN 0 AND total_marks),
        CONSTRAINT chk_grade_points CHECK (grade_points BETWEEN 0.00 AND 4.00))""",
    # audit_log
    """CREATE TABLE audit_log (
        log_id INT AUTO_INCREMENT PRIMARY KEY, table_name VARCHAR(50) NOT NULL,
        record_id INT NOT NULL, action ENUM('INSERT','UPDATE','DELETE') NOT NULL,
        old_value TEXT, new_value TEXT, changed_by INT,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_audit_changed_by FOREIGN KEY (changed_by) REFERENCES users(user_id) ON DELETE SET NULL)""",
    # Indexes
    "CREATE INDEX idx_enrollments_student ON enrollments(student_id)",
    "CREATE INDEX idx_enrollments_section ON enrollments(section_id)",
    "CREATE INDEX idx_enrollments_status ON enrollments(status)",
    "CREATE INDEX idx_attendance_date ON attendance(class_date)",
    "CREATE INDEX idx_cs_course ON course_sections(course_id)",
    "CREATE INDEX idx_cs_semester ON course_sections(semester_id)",
    "CREATE INDEX idx_cs_faculty ON course_sections(faculty_id)",
    "CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id)",
]

for s in schema_stmts:
    cursor.execute(s)
conn.commit()
print("✅ All tables + indexes created")

# ── Views ──
views = [
    """CREATE OR REPLACE VIEW v_student_transcript AS
    SELECT s.student_id, CONCAT(s.first_name,' ',s.last_name) AS student_name,
           c.course_code, c.course_name, c.credit_hours, cs.section_code,
           sm.name AS semester_name, g.marks_obtained, g.total_marks,
           g.letter_grade, g.grade_points, e.status AS enrollment_status, e.enrolled_at
    FROM students s JOIN enrollments e ON s.student_id=e.student_id
    JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN grades g ON e.enrollment_id=g.enrollment_id""",

    """CREATE OR REPLACE VIEW v_attendance_summary AS
    SELECT e.enrollment_id, e.student_id, e.section_id, c.course_name,
           cs.section_code, sm.name AS semester_name,
           COUNT(a.attendance_id) AS total_classes,
           SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS classes_attended,
           ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END)
                 /NULLIF(COUNT(a.attendance_id),0)*100,2) AS attendance_percentage
    FROM enrollments e JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN attendance a ON e.enrollment_id=a.enrollment_id
    GROUP BY e.enrollment_id, e.student_id, e.section_id, c.course_name, cs.section_code, sm.name""",

    """CREATE OR REPLACE VIEW v_course_roster AS
    SELECT c.course_id, c.course_code, c.course_name, cs.section_id, cs.section_code,
           sm.name AS semester_name, CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
           s.student_id, CONCAT(s.first_name,' ',s.last_name) AS student_name, s.email,
           e.enrollment_id, e.enrolled_at, e.status
    FROM course_sections cs JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    JOIN faculty f ON cs.faculty_id=f.faculty_id
    JOIN enrollments e ON cs.section_id=e.section_id
    JOIN students s ON e.student_id=s.student_id WHERE e.status='active'""",

    """CREATE OR REPLACE VIEW v_admin_enrollment_report AS
    SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
           cs.section_id, cs.section_code, sm.name AS semester_name,
           CONCAT(f.first_name,' ',f.last_name) AS faculty_name, cs.max_capacity,
           COUNT(e.enrollment_id) AS enrolled_count,
           cs.max_capacity-COUNT(e.enrollment_id) AS seats_remaining,
           ROUND(COUNT(e.enrollment_id)/cs.max_capacity*100,1) AS fill_percentage
    FROM course_sections cs JOIN courses c ON cs.course_id=c.course_id
    JOIN semesters sm ON cs.semester_id=sm.semester_id
    LEFT JOIN faculty f ON cs.faculty_id=f.faculty_id
    LEFT JOIN enrollments e ON cs.section_id=e.section_id AND e.status='active'
    GROUP BY c.course_id, c.course_code, c.course_name, c.credit_hours,
             cs.section_id, cs.section_code, sm.name, f.first_name, f.last_name, cs.max_capacity""",

    """CREATE OR REPLACE VIEW v_student_cgpa AS
    SELECT e.student_id,
           ROUND(SUM(g.grade_points*c.credit_hours)/NULLIF(SUM(c.credit_hours),0),2) AS cgpa
    FROM enrollments e JOIN grades g ON e.enrollment_id=g.enrollment_id
    JOIN course_sections cs ON e.section_id=cs.section_id
    JOIN courses c ON cs.course_id=c.course_id
    WHERE e.status='completed' AND g.grade_points IS NOT NULL
    GROUP BY e.student_id""",
]
for v in views:
    cursor.execute(v)
conn.commit()
print("✅ All views created")

# ── Triggers (no DELIMITER needed in Python) ──
triggers = [
    """CREATE TRIGGER trg_grade_before_insert BEFORE INSERT ON grades FOR EACH ROW
    BEGIN
        IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
            IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
            END IF;
        END IF;
    END""",

    """CREATE TRIGGER trg_grade_before_update BEFORE UPDATE ON grades FOR EACH ROW
    BEGIN
        IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
            IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
            END IF;
        END IF;
        IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL AND NEW.total_marks > 0 THEN
            SET @v_pct = (NEW.marks_obtained / NEW.total_marks) * 100;
            IF    @v_pct >= 90 THEN SET NEW.letter_grade='A',  NEW.grade_points=4.00;
            ELSEIF @v_pct >= 85 THEN SET NEW.letter_grade='A-', NEW.grade_points=3.70;
            ELSEIF @v_pct >= 80 THEN SET NEW.letter_grade='B+', NEW.grade_points=3.30;
            ELSEIF @v_pct >= 75 THEN SET NEW.letter_grade='B',  NEW.grade_points=3.00;
            ELSEIF @v_pct >= 70 THEN SET NEW.letter_grade='B-', NEW.grade_points=2.70;
            ELSEIF @v_pct >= 65 THEN SET NEW.letter_grade='C+', NEW.grade_points=2.30;
            ELSEIF @v_pct >= 60 THEN SET NEW.letter_grade='C',  NEW.grade_points=2.00;
            ELSE                     SET NEW.letter_grade='F',  NEW.grade_points=0.00;
            END IF;
        END IF;
    END""",

    """CREATE TRIGGER trg_grade_audit_update AFTER UPDATE ON grades FOR EACH ROW
    BEGIN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES ('grades', NEW.grade_id, 'UPDATE',
                CONCAT('marks=', OLD.marks_obtained, ', grade=', IFNULL(OLD.letter_grade, 'NULL')),
                CONCAT('marks=', NEW.marks_obtained, ', grade=', IFNULL(NEW.letter_grade, 'NULL')), NULL);
    END""",

    """CREATE TRIGGER trg_attendance_audit_update AFTER UPDATE ON attendance FOR EACH ROW
    BEGIN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES ('attendance', NEW.attendance_id, 'UPDATE',
                CONCAT('status=', OLD.status), CONCAT('status=', NEW.status), NEW.marked_by);
    END""",

    """CREATE TRIGGER trg_attendance_before_insert BEFORE INSERT ON attendance FOR EACH ROW
    BEGIN
        IF NEW.class_date > CURDATE() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
        END IF;
    END""",

    """CREATE TRIGGER trg_attendance_before_update BEFORE UPDATE ON attendance FOR EACH ROW
    BEGIN
        IF NEW.class_date > CURDATE() THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
        END IF;
    END""",
]
for t in triggers:
    cursor.execute(t)
conn.commit()
print("✅ All triggers created")

# ── Stored Procedures ──
sps = [
    """CREATE PROCEDURE RegisterStudentInCourse(
        IN p_student_id INT, IN p_section_id INT,
        OUT p_message VARCHAR(255), OUT p_success TINYINT)
    BEGIN
        DECLARE v_count INT DEFAULT 0; DECLARE v_enrolled_cnt INT DEFAULT 0; DECLARE v_capacity INT DEFAULT 0;
        SELECT COUNT(*) INTO v_count FROM enrollments WHERE student_id=p_student_id AND section_id=p_section_id AND status='active';
        IF v_count > 0 THEN SET p_message='Student is already enrolled in this section.'; SET p_success=0;
        ELSE
            SELECT max_capacity INTO v_capacity FROM course_sections WHERE section_id=p_section_id;
            SELECT COUNT(*) INTO v_enrolled_cnt FROM enrollments WHERE section_id=p_section_id AND status='active';
            IF v_enrolled_cnt >= v_capacity THEN SET p_message='Section is full. Enrollment not allowed.'; SET p_success=0;
            ELSE
                INSERT INTO enrollments (student_id, section_id, status) VALUES (p_student_id, p_section_id, 'active');
                INSERT INTO grades (enrollment_id) VALUES (LAST_INSERT_ID());
                SET p_message='Enrollment successful.'; SET p_success=1;
            END IF;
        END IF;
    END""",

    """CREATE PROCEDURE CalculateStudentGPA(IN p_student_id INT, OUT p_gpa DECIMAL(3,2))
    BEGIN
        DECLARE v_total_points DECIMAL(10,2) DEFAULT 0; DECLARE v_total_credits INT DEFAULT 0;
        SELECT SUM(g.grade_points*c.credit_hours), SUM(c.credit_hours)
        INTO v_total_points, v_total_credits
        FROM enrollments e JOIN grades g ON e.enrollment_id=g.enrollment_id
        JOIN course_sections cs ON e.section_id=cs.section_id
        JOIN courses c ON cs.course_id=c.course_id
        WHERE e.student_id=p_student_id AND e.status='completed' AND g.grade_points IS NOT NULL;
        IF v_total_credits=0 OR v_total_credits IS NULL THEN SET p_gpa=0.00;
        ELSE SET p_gpa=ROUND(v_total_points/v_total_credits,2); END IF;
    END""",

    """CREATE PROCEDURE UpdateLetterGrade(IN p_enrollment_id INT)
    BEGIN
        DECLARE v_percentage DECIMAL(5,2); DECLARE v_letter CHAR(2); DECLARE v_points DECIMAL(3,2);
        SELECT (marks_obtained/total_marks*100) INTO v_percentage FROM grades WHERE enrollment_id=p_enrollment_id;
        IF v_percentage >= 90 THEN SET v_letter='A', v_points=4.00;
        ELSEIF v_percentage >= 85 THEN SET v_letter='A-', v_points=3.70;
        ELSEIF v_percentage >= 80 THEN SET v_letter='B+', v_points=3.30;
        ELSEIF v_percentage >= 75 THEN SET v_letter='B', v_points=3.00;
        ELSEIF v_percentage >= 70 THEN SET v_letter='B-', v_points=2.70;
        ELSEIF v_percentage >= 65 THEN SET v_letter='C+', v_points=2.30;
        ELSEIF v_percentage >= 60 THEN SET v_letter='C', v_points=2.00;
        ELSE SET v_letter='F', v_points=0.00; END IF;
        UPDATE grades SET letter_grade=v_letter, grade_points=v_points WHERE enrollment_id=p_enrollment_id;
    END""",
]
for sp in sps:
    cursor.execute(sp)
conn.commit()
print("✅ All stored procedures created")

# ── Seed Data ──
seed = [
    """INSERT INTO users (user_id, username, password, role, is_active) VALUES
    (1,'admin_ali','$2b$12$X7j3wqA1x1L2Y8N0mQeR1uJkD4h6p9s2t5v8w0y3z6A9bC1dE2fG','admin',TRUE),
    (2,'admin_sara','$2b$12$Q1w2e3r4t5y6u7i8o9p0aSDFGHJKLZXCVBNMqwertyuiopasdfgh','admin',TRUE),
    (3,'f_khan','$2b$12$hG4kP1aQ9mN8vC7xZ6lT5rE3wS2dF1gH0jK9lP8oI7uY6tR5eW4q','faculty',TRUE),
    (4,'f_mehmood','$2b$12$jD3sA7pL0qW9eR4tY6uI8oP2aS5dF7gH1jK3lZ6xC9vB2nM4qW8r','faculty',TRUE),
    (5,'f_rizvi','$2b$12$kL9pO4iU1yT8rE6wQ3aS7dF2gH5jK0lZ4xC8vB1nM6qW9eR3tY7u','faculty',TRUE),
    (6,'f_nadeem','$2b$12$mN2bV6cX9zA1sD4fG7hJ0kL3pO8iU5yT2rE6wQ9aS3dF7gH1jK4l','faculty',TRUE),
    (7,'s_hassan','$2b$12$nB7vC3xZ0aS5dF9gH2jK6lP1oI4uY8tR3eW7qA2sD6fG0hJ5kL9p','student',TRUE),
    (8,'s_fatima','$2b$12$pO1iU5yT9rE2wQ6aS0dF4gH8jK3lZ7xC1vB5nM9qW2eR6tY0uI4o','student',TRUE),
    (9,'s_usman','$2b$12$qW8eR3tY7uI1oP5aS9dF2gH6jK0lZ4xC8vB2nM6qW1eR5tY9uI3o','student',TRUE),
    (10,'s_maryam','$2b$12$rT4yU8iO2pA6sD0fG5hJ9kL3zX7cV1bN4mQ8wE2rT6yU0iO5pA9s','student',TRUE)""",

    """INSERT INTO students (student_id, user_id, first_name, last_name, email, dob, program, batch_year) VALUES
    (1,7,'Hassan','Raza','hassan.raza@student.smartcampus.edu','2004-03-14','BS Computer Science',2022),
    (2,8,'Fatima','Noor','fatima.noor@student.smartcampus.edu','2003-11-22','BS Information Technology',2021),
    (3,9,'Usman','Iqbal','usman.iqbal@student.smartcampus.edu','2004-07-09','BBA',2022),
    (4,10,'Maryam','Saleem','maryam.saleem@student.smartcampus.edu','2005-01-30','BS Software Engineering',2023)""",

    """INSERT INTO faculty (faculty_id, user_id, first_name, last_name, email, department, designation) VALUES
    (1,3,'Adeel','Khan','adeel.khan@smartcampus.edu','Computer Science','Assistant Professor'),
    (2,4,'Hina','Mehmood','hina.mehmood@smartcampus.edu','Information Systems','Lecturer'),
    (3,5,'Bilal','Rizvi','bilal.rizvi@smartcampus.edu','Business School','Associate Professor'),
    (4,6,'Samina','Nadeem','samina.nadeem@smartcampus.edu','Software Engineering','Assistant Professor')""",

    """INSERT INTO courses (course_id, course_code, course_name, credit_hours) VALUES
    (1,'CS101','Introduction to Programming',3),(2,'CS205','Database Systems',3),
    (3,'IT220','Web Application Development',3),(4,'IS310','Management Information Systems',3),
    (5,'BBA201','Principles of Marketing',3),(6,'BBA305','Business Analytics',3),
    (7,'SE240','Software Design and Architecture',3),(8,'SE315','Software Quality Assurance',3)""",

    "INSERT INTO semesters (semester_id, name, start_date, end_date, is_active) VALUES (1,'Fall 2026','2026-08-01','2026-12-31',TRUE)",

    """INSERT INTO course_sections (section_id, course_id, semester_id, faculty_id, section_code, max_capacity) VALUES
    (1,1,1,1,'A',50),(2,2,1,1,'A',45),(3,3,1,2,'A',40),(4,4,1,2,'A',35),
    (5,5,1,3,'A',60),(6,6,1,3,'A',40),(7,7,1,4,'A',40),(8,8,1,4,'A',35)""",

    """INSERT INTO enrollments (enrollment_id, student_id, section_id, enrolled_at, status) VALUES
    (1,1,1,'2026-08-20 09:10:00','active'),(2,1,2,'2026-08-20 09:12:00','active'),
    (3,1,3,'2026-08-20 09:14:00','active'),(4,2,2,'2026-08-21 10:00:00','active'),
    (5,2,4,'2026-08-21 10:02:00','active'),(6,2,7,'2026-08-21 10:04:00','active'),
    (7,3,5,'2026-08-22 11:20:00','active'),(8,3,6,'2026-08-22 11:22:00','completed'),
    (9,4,1,'2026-08-23 12:00:00','active'),(10,4,8,'2026-08-23 12:02:00','active')""",

    """INSERT INTO attendance (attendance_id, enrollment_id, class_date, status, marked_by) VALUES
    (1,1,'2026-03-01','present',3),(2,2,'2026-03-01','present',3),
    (3,3,'2026-03-01','late',4),(4,4,'2026-03-02','present',3),
    (5,5,'2026-03-02','absent',4),(6,6,'2026-03-02','present',6),
    (7,7,'2026-03-03','present',5),(8,8,'2026-03-03','present',5),
    (9,9,'2026-03-04','late',3),(10,10,'2026-03-04','present',6)""",

    """INSERT INTO grades (grade_id, enrollment_id, marks_obtained, total_marks, letter_grade, grade_points) VALUES
    (1,1,86.50,100.00,'A-',3.70),(2,2,79.00,100.00,'B',3.00),
    (3,3,74.00,100.00,'B-',2.70),(4,4,91.00,100.00,'A',4.00),
    (5,5,83.00,100.00,'B+',3.30),(6,6,88.50,100.00,'A-',3.70),
    (7,7,72.00,100.00,'B-',2.70),(8,8,69.00,100.00,'C+',2.30),
    (9,9,94.00,100.00,'A',4.00),(10,10,81.00,100.00,'B+',3.30)""",
]
for s in seed:
    cursor.execute(s)
conn.commit()
print("✅ Seed data inserted")

# Verify
cursor.execute("SELECT COUNT(*) FROM course_sections")
print(f"   course_sections: {cursor.fetchone()[0]} rows")
cursor.execute("SELECT COUNT(*) FROM enrollments")
print(f"   enrollments: {cursor.fetchone()[0]} rows")
cursor.execute("SELECT * FROM v_student_cgpa")
rows = cursor.fetchall()
print(f"   v_student_cgpa: {len(rows)} rows → {rows}")
cursor.execute("SHOW TABLES")
tables = [r[0] for r in cursor.fetchall()]
print(f"   Tables: {tables}")

cursor.close()
conn.close()
print("\n✅ DATABASE REBUILD COMPLETE")
