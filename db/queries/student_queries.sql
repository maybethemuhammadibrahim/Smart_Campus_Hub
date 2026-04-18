-- Q1: Full transcript for a specific student
SELECT * FROM v_student_transcript WHERE student_id = ?;

-- Q2: Attendance percentage per course for a student
SELECT * FROM v_attendance_summary WHERE student_id = ?;

-- Q3: Available courses not yet enrolled in
SELECT c.course_id, c.course_code, c.course_name, c.credit_hours,
       CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
       c.max_capacity - COUNT(e.enrollment_id) AS seats_left
FROM courses c
LEFT JOIN faculty     f ON c.faculty_id = f.faculty_id
LEFT JOIN enrollments e ON c.course_id  = e.course_id
    AND e.status = 'active'
WHERE c.course_id NOT IN (
    SELECT course_id FROM enrollments
    WHERE student_id = ? AND status = 'active'
)
GROUP BY c.course_id, c.course_code, c.course_name,
         c.credit_hours, f.first_name, f.last_name, c.max_capacity
HAVING seats_left > 0;