-- Q1: Course roster (use view)
SELECT * FROM v_course_roster WHERE course_id = ?;

-- Q2: Average marks per course
SELECT
    c.course_name,
    AVG(g.marks_obtained)  AS avg_marks,
    MAX(g.marks_obtained)  AS highest_marks,
    MIN(g.marks_obtained)  AS lowest_marks,
    COUNT(e.enrollment_id) AS total_students
FROM courses     c
JOIN enrollments e ON c.course_id     = e.course_id
JOIN grades      g ON e.enrollment_id = g.enrollment_id
WHERE c.course_id = ?
GROUP BY c.course_name;

-- Q3: Students with attendance below 75%
SELECT
    s.student_id,
    CONCAT(s.first_name,' ',s.last_name) AS student_name,
    s.email,
    att.attendance_percentage
FROM v_attendance_summary att
JOIN students s ON att.student_id = s.student_id
WHERE att.course_id = ?
  AND att.attendance_percentage < 75
ORDER BY att.attendance_percentage ASC;