-- Q1: Enrollment report (use view)
SELECT * FROM v_admin_enrollment_report ORDER BY enrolled_count DESC;

-- Q2: GPA distribution (histogram buckets)
SELECT
    CASE
        WHEN cgpa >= 3.5 THEN '3.5 - 4.0 (Dean''s List)'
        WHEN cgpa >= 3.0 THEN '3.0 - 3.49 (Good)'
        WHEN cgpa >= 2.5 THEN '2.5 - 2.99 (Satisfactory)'
        WHEN cgpa >= 2.0 THEN '2.0 - 2.49 (Passing)'
        ELSE                   'Below 2.0 (At Risk)'
    END              AS gpa_range,
    COUNT(student_id) AS student_count
FROM students
GROUP BY gpa_range
ORDER BY MIN(cgpa) DESC;

-- Q3: Courses taught by each faculty with enrollment count
SELECT
    CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
    f.department,
    COUNT(DISTINCT c.course_id)           AS courses_teaching,
    SUM(sub.enrolled)                     AS total_students
FROM faculty f
JOIN courses c ON f.faculty_id = c.faculty_id
JOIN (
    SELECT course_id, COUNT(*) AS enrolled
    FROM enrollments WHERE status='active'
    GROUP BY course_id
) sub ON c.course_id = sub.course_id
GROUP BY f.faculty_id, f.first_name, f.last_name, f.department
ORDER BY total_students DESC;