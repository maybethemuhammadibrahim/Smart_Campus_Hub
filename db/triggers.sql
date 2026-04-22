USE smart_campus;
DELIMITER $$

-- ============================================================
-- TRIGGER 1: Validate grades before INSERT
-- Ensures marks_obtained does not exceed total_marks
-- ============================================================
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

-- ============================================================
-- TRIGGER 2: Validate grades before UPDATE
-- Ensures marks_obtained does not exceed total_marks
-- ============================================================
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

-- ============================================================
-- TRIGGER 3: Auto-call UpdateLetterGrade when marks are updated
-- ============================================================
CREATE TRIGGER trg_grade_after_update
AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained <> OLD.marks_obtained THEN
        CALL UpdateLetterGrade(NEW.enrollment_id);
    END IF;
END$$

-- ============================================================
-- TRIGGER 4: Audit log for grade changes
-- Tracks all modifications to student grades
-- ============================================================
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

-- ============================================================
-- TRIGGER 5: Audit log for attendance changes
-- Tracks all modifications to attendance records
-- ============================================================
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

-- ============================================================
-- TRIGGER 6: Prevent future attendance dates
-- ============================================================
CREATE TRIGGER trg_attendance_before_insert
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    IF NEW.class_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot mark attendance for a future date';
    END IF;
END$$

DELIMITER ;