USE smart_campus;
DELIMITER $$

-- Trigger: Auto-call UpdateLetterGrade when marks are updated
CREATE TRIGGER trg_grade_after_update
AFTER UPDATE ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained <> OLD.marks_obtained THEN
        CALL UpdateLetterGrade(NEW.enrollment_id);
    END IF;
END$$

DELIMITER ;