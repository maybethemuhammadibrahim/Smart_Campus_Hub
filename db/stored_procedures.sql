USE smart_campus;
DELIMITER $$

CREATE PROCEDURE RegisterStudentInCourse(
    IN  p_student_id INT,
    IN  p_section_id INT,
    OUT p_message    VARCHAR(255),
    OUT p_success    TINYINT
)
BEGIN
    DECLARE v_count              INT     DEFAULT 0;
    DECLARE v_enrolled_cnt       INT     DEFAULT 0;
    DECLARE v_capacity           INT     DEFAULT 0;
    DECLARE v_enrollment_id      INT     DEFAULT 0;
    DECLARE v_course_id          INT     DEFAULT NULL;
    DECLARE v_semester_id        INT     DEFAULT NULL;
    DECLARE v_same_course_cnt    INT     DEFAULT 0;   -- rule 1
    DECLARE v_active_course_cnt  INT     DEFAULT 0;   -- rule 2

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Unexpected database error during enrollment. Transaction rolled back.';
        SET p_success = 0;
    END;

    START TRANSACTION;

    SELECT max_capacity, course_id, semester_id
    INTO   v_capacity, v_course_id, v_semester_id
    FROM   course_sections
    WHERE  section_id = p_section_id
    FOR UPDATE;                        

    SELECT COUNT(*) INTO v_enrolled_cnt
    FROM enrollments
    WHERE section_id = p_section_id
      AND status = 'active';

    SELECT COUNT(*) INTO v_count
    FROM enrollments
    WHERE student_id = p_student_id
      AND section_id = p_section_id
      AND status = 'active';

    SELECT COUNT(*) INTO v_same_course_cnt
    FROM   enrollments   e
    JOIN   course_sections cs ON e.section_id = cs.section_id
    WHERE  e.student_id  = p_student_id
      AND  e.status       = 'active'
      AND  cs.course_id   = v_course_id
      AND  cs.semester_id = v_semester_id;
    
    SELECT COUNT(*) INTO v_active_course_cnt
    FROM   enrollments   e
    JOIN   course_sections cs ON e.section_id = cs.section_id
    WHERE  e.student_id  = p_student_id
      AND  e.status       = 'active'
      AND  cs.semester_id = v_semester_id;

    IF v_count > 0 THEN
        ROLLBACK;
        SET p_message = 'Student is already enrolled in this section.';
        SET p_success = 0;

    ELSEIF v_same_course_cnt >= 1 THEN
        ROLLBACK;
        SET p_message = 'Enrollment rejected: already enrolled in another section of this course this semester.';
        SET p_success = 0;

    ELSEIF v_active_course_cnt >= 6 THEN
        ROLLBACK;
        SET p_message = 'Enrollment rejected: maximum of 6 active courses per semester already reached.';
        SET p_success = 0;

    ELSEIF v_enrolled_cnt >= v_capacity THEN
        ROLLBACK;
        SET p_message = 'Section is full. Enrollment not allowed.';
        SET p_success = 0;

    ELSE
        INSERT INTO enrollments (student_id, section_id, status)
        VALUES (p_student_id, p_section_id, 'active');

        SET v_enrollment_id = LAST_INSERT_ID();

        INSERT INTO grades (enrollment_id)
        VALUES (v_enrollment_id);

        COMMIT;
        SET p_message = 'Enrollment successful.';
        SET p_success = 1;
    END IF;
END$$


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
    FROM enrollments     e
    JOIN grades          g  ON e.enrollment_id = g.enrollment_id
    JOIN course_sections cs ON e.section_id   = cs.section_id
    JOIN courses         c  ON cs.course_id   = c.course_id
    WHERE e.student_id = p_student_id
      AND e.status = 'completed'
      AND g.grade_points IS NOT NULL;

    IF v_total_credits = 0 OR v_total_credits IS NULL THEN
        SET p_gpa = 0.00;
    ELSE
        SET p_gpa = ROUND(v_total_points / v_total_credits, 2);
    END IF;
    -- return cgpa via param
END$$


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


CREATE PROCEDURE DropEnrollment(
    IN  p_enrollment_id  INT,
    IN  p_changed_by     INT,        -- actor id
    OUT p_message        VARCHAR(255),
    OUT p_success        TINYINT
)
BEGIN
    DECLARE v_current_status VARCHAR(20) DEFAULT NULL;
    DECLARE v_marks          DECIMAL(5,2) DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Unexpected error during drop. Transaction rolled back.';
        SET p_success = 0;
    END;

    START TRANSACTION;

    -- lock row
    SELECT status INTO v_current_status
    FROM enrollments
    WHERE enrollment_id = p_enrollment_id
    FOR UPDATE;

    IF v_current_status IS NULL THEN
        ROLLBACK;
        SET p_message = 'Enrollment not found.';
        SET p_success = 0;

    ELSEIF v_current_status <> 'active' THEN
        ROLLBACK;
        SET p_message = CONCAT('Cannot drop: enrollment is already "', v_current_status, '".');
        SET p_success = 0;

    ELSE
        -- set status dropped
        UPDATE enrollments
        SET status = 'dropped'
        WHERE enrollment_id = p_enrollment_id;

        -- clear placeholder grade
        SELECT IFNULL(marks_obtained, 0) INTO v_marks
        FROM grades
        WHERE enrollment_id = p_enrollment_id;

        IF v_marks = 0 THEN
            UPDATE grades
            SET marks_obtained = NULL,
                letter_grade   = NULL,
                grade_points   = NULL
            WHERE enrollment_id = p_enrollment_id;
        END IF;

        -- write audit
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES (
            'enrollments',
            p_enrollment_id,
            'UPDATE',
            'status=active',
            'status=dropped',
            p_changed_by
        );

        COMMIT;
        SET p_message = 'Enrollment dropped successfully.';
        SET p_success = 1;
    END IF;
END$$


CREATE PROCEDURE BulkCompleteEnrollments(
    IN  p_section_id  INT,
    IN  p_changed_by  INT,         -- admin id
    OUT p_completed   INT,         -- count
    OUT p_message     VARCHAR(255)
)
BEGIN
    DECLARE v_enrollment_id INT;
    DECLARE v_done          TINYINT DEFAULT 0;

    -- active enrollments cursor
    DECLARE cur_active CURSOR FOR
        SELECT enrollment_id
        FROM enrollments
        WHERE section_id = p_section_id
          AND status = 'active';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_message = 'Unexpected error during bulk completion. All changes rolled back.';
        SET p_completed = 0;
    END;

    SET p_completed = 0;

    START TRANSACTION;

    SELECT section_id FROM course_sections
    WHERE section_id = p_section_id
    FOR UPDATE;

    OPEN cur_active;

    complete_loop: LOOP
        FETCH cur_active INTO v_enrollment_id;

        IF v_done = 1 THEN
            LEAVE complete_loop;
        END IF;

        -- set status completed
        UPDATE enrollments
        SET status = 'completed'
        WHERE enrollment_id = v_enrollment_id;

        -- log completion
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES (
            'enrollments',
            v_enrollment_id,
            'UPDATE',
            'status=active',
            'status=completed',
            p_changed_by
        );

        SET p_completed = p_completed + 1;
    END LOOP;

    CLOSE cur_active;

    COMMIT;
    SET p_message = CONCAT(p_completed, ' enrollment(s) marked as completed.');
END$$

DELIMITER ;
