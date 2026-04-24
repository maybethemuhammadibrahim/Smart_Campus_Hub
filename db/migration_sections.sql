-- ============================================================
-- Migration: Add section support to courses table
-- Run this ONCE on your existing database
-- ============================================================
USE smart_campus;

-- 1. Add section column (default 'A' for existing rows)
ALTER TABLE courses ADD COLUMN section VARCHAR(10) NOT NULL DEFAULT 'A' AFTER semester;

-- 2. Drop old unique constraint on course_code
ALTER TABLE courses DROP INDEX course_code;

-- 3. Add new unique constraint on (course_code, section, semester)
ALTER TABLE courses ADD CONSTRAINT uq_course_section UNIQUE (course_code, section, semester);

-- 4. Add index on (course_code, section)
CREATE INDEX idx_courses_section ON courses(course_code, section);

-- 5. Drop the broken AFTER UPDATE trigger that causes Error 1442
DROP TRIGGER IF EXISTS trg_grade_after_update;

-- 6. Create the fixed BEFORE UPDATE trigger (auto letter grade)
DELIMITER $$
CREATE TRIGGER trg_grade_before_update_v2
BEFORE UPDATE ON grades
FOR EACH ROW
BEGIN
    -- Validate marks range
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
        IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
        END IF;
    END IF;

    -- Auto-compute letter grade when marks change
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL
       AND NEW.total_marks > 0 THEN
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
END$$

-- 7. Drop the old BEFORE UPDATE trigger (validation only) since v2 handles both
DROP TRIGGER IF EXISTS trg_grade_before_update$$

-- 8. Rename v2 to the proper name
-- MySQL doesn't support RENAME TRIGGER, so v2 stays as is

-- 9. Add section-limit trigger
CREATE TRIGGER trg_course_section_limit
BEFORE INSERT ON courses
FOR EACH ROW
BEGIN
    DECLARE v_count INT DEFAULT 0;
    IF NEW.faculty_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_count
        FROM courses
        WHERE faculty_id  = NEW.faculty_id
          AND course_code = NEW.course_code
          AND semester    = NEW.semester;
        IF v_count >= 3 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faculty cannot teach more than 3 sections of the same course per semester';
        END IF;
    END IF;
END$$

DELIMITER ;

-- 10. Add multi-section sample data
INSERT INTO courses (course_code, course_name, credit_hours, semester, section, faculty_id, max_capacity) VALUES
('CS101',  'Introduction to Programming',  3, 'Fall 2026', 'B', 1, 45),
('IT220',  'Web Application Development',  3, 'Fall 2026', 'B', 2, 35);

-- 11. Add enrollments for new sections
INSERT INTO enrollments (student_id, course_id, enrolled_at, status) VALUES
(3, (SELECT course_id FROM courses WHERE course_code='CS101' AND section='B'), '2026-08-22 11:30:00', 'active'),
(4, (SELECT course_id FROM courses WHERE course_code='IT220' AND section='B'), '2026-08-23 12:05:00', 'active');

-- 12. Add grades for new enrollments
INSERT INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points)
SELECT e.enrollment_id, 67.00, 100.00, 'C+', 2.30
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
WHERE c.course_code = 'CS101' AND c.section = 'B' AND e.student_id = 3;

INSERT INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points)
SELECT e.enrollment_id, 78.00, 100.00, 'B', 3.00
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
WHERE c.course_code = 'IT220' AND c.section = 'B' AND e.student_id = 4;

-- 13. Recreate views with section column
CREATE OR REPLACE VIEW v_student_transcript AS
SELECT
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name)  AS student_name,
    c.course_code,
    c.course_name,
    c.section,
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

CREATE OR REPLACE VIEW v_attendance_summary AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.course_id,
    c.course_name,
    c.section,
    COUNT(a.attendance_id)                                     AS total_classes,
    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)     AS classes_attended,
    ROUND(
        SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(a.attendance_id), 0) * 100, 2
    )                                                          AS attendance_percentage
FROM enrollments e
JOIN courses     c ON e.course_id = c.course_id
LEFT JOIN attendance a ON e.enrollment_id = a.enrollment_id
GROUP BY e.enrollment_id, e.student_id, e.course_id, c.course_name, c.section;

CREATE OR REPLACE VIEW v_course_roster AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    c.section,
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

CREATE OR REPLACE VIEW v_admin_enrollment_report AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    c.section,
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
         c.section, c.credit_hours, f.first_name, f.last_name,
         c.max_capacity;

SELECT '✅ Migration completed successfully!' AS status;
