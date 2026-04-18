USE smart_campus;

-- ============================================================
-- VIEW 1: v_student_transcript
-- Full academic record per student — covers Ch.7 Views
-- Uses: JOIN, aggregate, GROUP BY
-- ============================================================
CREATE OR REPLACE VIEW v_student_transcript AS
SELECT
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name)  AS student_name,
    c.course_code,
    c.course_name,
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

-- ============================================================
-- VIEW 2: v_attendance_summary
-- Attendance % per student per course — covers aggregation
-- ============================================================
CREATE OR REPLACE VIEW v_attendance_summary AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.course_id,
    c.course_name,
    COUNT(a.attendance_id)                                     AS total_classes,
    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)     AS classes_attended,
    ROUND(
        SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(a.attendance_id), 0) * 100, 2
    )                                                          AS attendance_percentage
FROM enrollments e
JOIN courses     c ON e.course_id = c.course_id
LEFT JOIN attendance a ON e.enrollment_id = a.enrollment_id
GROUP BY e.enrollment_id, e.student_id, e.course_id, c.course_name;

-- ============================================================
-- VIEW 3: v_course_roster
-- List of students enrolled in each course — faculty use
-- ============================================================
CREATE OR REPLACE VIEW v_course_roster AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
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

-- ============================================================
-- VIEW 4: v_admin_enrollment_report
-- Total students enrolled in each course — admin report
-- ============================================================
CREATE OR REPLACE VIEW v_admin_enrollment_report AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
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
         c.credit_hours, f.first_name, f.last_name,
         c.max_capacity;