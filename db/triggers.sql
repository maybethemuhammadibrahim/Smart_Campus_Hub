USE smart_campus;
DELIMITER $$

CREATE TRIGGER trg_grade_before_insert
BEFORE INSERT ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
        IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
        END IF;
    END IF;
END$$


CREATE TRIGGER trg_grade_before_update
BEFORE UPDATE ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
        IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
        END IF;
    END IF;
END$$


CREATE TRIGGER trg_grade_audit_update
AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
    VALUES (
        'grades',
        NEW.grade_id,
        'UPDATE',
        CONCAT('marks=', OLD.marks_obtained, ', grade=', IFNULL(OLD.letter_grade, 'NULL')),
        CONCAT('marks=', NEW.marks_obtained, ', grade=', IFNULL(NEW.letter_grade, 'NULL')),
        NULL
    );
END$$


CREATE TRIGGER trg_attendance_audit_update
AFTER UPDATE ON attendance
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
    VALUES (
        'attendance',
        NEW.attendance_id,
        'UPDATE',
        CONCAT('status=', OLD.status),
        CONCAT('status=', NEW.status),
        NEW.marked_by
    );
END$$

CREATE TRIGGER trg_attendance_before_insert
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END$$


CREATE TRIGGER trg_attendance_before_update
BEFORE UPDATE ON attendance
FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END$$


CREATE TRIGGER trg_faculty_load_insert
BEFORE INSERT ON course_sections
FOR EACH ROW
BEGIN
    DECLARE v_count INT;
    IF NEW.faculty_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_count
        FROM course_sections
        WHERE faculty_id = NEW.faculty_id
          AND semester_id = NEW.semester_id;
        
        IF v_count >= 6 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faculty cannot be assigned more than 6 sections per semester.';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_faculty_load_update
BEFORE UPDATE ON course_sections
FOR EACH ROW
BEGIN
    DECLARE v_count INT;
    IF NEW.faculty_id IS NOT NULL AND NEW.faculty_id != OLD.faculty_id THEN
        SELECT COUNT(*) INTO v_count
        FROM course_sections
        WHERE faculty_id = NEW.faculty_id
          AND semester_id = NEW.semester_id;
        
        IF v_count >= 6 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faculty cannot be assigned more than 6 sections per semester.';
        END IF;
    END IF;
END$$


CREATE TRIGGER trg_enrollment_capacity_guard
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_capacity     SMALLINT DEFAULT 0;
    DECLARE v_enrolled_cnt INT      DEFAULT 0;

    -- enforce for active
    IF NEW.status = 'active' THEN
        SELECT max_capacity INTO v_capacity
        FROM course_sections
        WHERE section_id = NEW.section_id;

        SELECT COUNT(*) INTO v_enrolled_cnt
        FROM enrollments
        WHERE section_id = NEW.section_id
          AND status = 'active';

        IF v_enrolled_cnt >= v_capacity THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Section capacity exceeded. Enrollment blocked by DB trigger.';
        END IF;
    END IF;
END$$


CREATE TRIGGER trg_enrollment_active_semester_check
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_is_active BOOLEAN DEFAULT FALSE;

    SELECT sm.is_active INTO v_is_active
    FROM course_sections cs
    JOIN semesters sm ON cs.semester_id = sm.semester_id
    WHERE cs.section_id = NEW.section_id;

    IF v_is_active = FALSE THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot enroll: the target semester is not currently active.';
    END IF;
END$$


CREATE TRIGGER trg_grade_after_insert_audit
AFTER INSERT ON grades
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
    VALUES (
        'grades',
        NEW.grade_id,
        'INSERT',
        NULL,
        CONCAT('enrollment_id=', NEW.enrollment_id,
               ', marks=', IFNULL(NEW.marks_obtained, 'NULL'),
               ', grade=', IFNULL(NEW.letter_grade, 'NULL')),
        NULL   -- set by app
    );
END$$


CREATE TRIGGER trg_enrollment_after_update_audit
AFTER UPDATE ON enrollments
FOR EACH ROW
BEGIN
    -- log on status change
    IF OLD.status <> NEW.status THEN
        INSERT INTO audit_log (table_name, record_id, action, old_value, new_value, changed_by)
        VALUES (
            'enrollments',
            NEW.enrollment_id,
            'UPDATE',
            CONCAT('status=', OLD.status,
                   ', student_id=', OLD.student_id,
                   ', section_id=', OLD.section_id),
            CONCAT('status=', NEW.status,
                   ', student_id=', NEW.student_id,
                   ', section_id=', NEW.section_id),
            NULL
        );
    END IF;
END$$


CREATE TRIGGER trg_enrollment_before_delete_guard
BEFORE DELETE ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_has_grade TINYINT DEFAULT 0;

    SELECT COUNT(*) INTO v_has_grade
    FROM grades
    WHERE enrollment_id = OLD.enrollment_id
      AND (marks_obtained IS NOT NULL AND marks_obtained > 0);

    IF v_has_grade > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot hard-delete an enrollment that already has grade data. Use DropEnrollment procedure instead.';
    END IF;
END$$


CREATE TRIGGER trg_enrollment_no_duplicate_course_in_semester
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_course_id        INT DEFAULT NULL;
    DECLARE v_semester_id      INT DEFAULT NULL;
    DECLARE v_existing_sections INT DEFAULT 0;

    -- check active status
    IF NEW.status = 'active' THEN
        -- resolve course semester
        SELECT cs.course_id, cs.semester_id
        INTO   v_course_id, v_semester_id
        FROM   course_sections cs
        WHERE  cs.section_id = NEW.section_id;

        -- count active enrollments
        SELECT COUNT(*) INTO v_existing_sections
        FROM   enrollments   e
        JOIN   course_sections cs ON e.section_id = cs.section_id
        WHERE  e.student_id  = NEW.student_id
          AND  e.status       = 'active'
          AND  cs.course_id   = v_course_id
          AND  cs.semester_id = v_semester_id;

        IF v_existing_sections >= 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Enrollment rejected: student is already enrolled in another section of this course in the same semester.';
        END IF;
    END IF;
END$$


CREATE TRIGGER trg_enrollment_max_courses_per_semester
BEFORE INSERT ON enrollments
FOR EACH ROW
BEGIN
    DECLARE v_semester_id    INT DEFAULT NULL;
    DECLARE v_active_courses INT DEFAULT 0;

    IF NEW.status = 'active' THEN
        -- find target semester
        SELECT semester_id INTO v_semester_id
        FROM   course_sections
        WHERE  section_id = NEW.section_id;

        -- count distinct active
        SELECT COUNT(*) INTO v_active_courses
        FROM   enrollments   e
        JOIN   course_sections cs ON e.section_id = cs.section_id
        WHERE  e.student_id  = NEW.student_id
          AND  e.status       = 'active'
          AND  cs.semester_id = v_semester_id;

        IF v_active_courses >= 6 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Enrollment rejected: student has reached the maximum of 6 active courses per semester.';
        END IF;
    END IF;
END$$

DELIMITER ;