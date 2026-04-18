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