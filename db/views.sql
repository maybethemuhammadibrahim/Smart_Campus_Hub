USE smart_campus;

-- ============================================================
-- VIEW 1: v_student_transcript
-- Full academic record per student — covers Ch.7 Views
-- Uses: JOIN, aggregate, GROUP BY
-- Joins through course_sections to resolve section → course
-- ============================================================
CREATE OR REPLACE VIEW v_student_transcript AS
SELECT
    s.student_id,
    CONCAT(s.first_name, ' ', s.last_name)  AS student_name,
    c.course_code,
    c.course_name,
    c.credit_hours,
    cs.section_code,
    sm.name                                  AS semester_name,
    g.marks_obtained,
    g.total_marks,
    g.letter_grade,
    g.grade_points,
    e.status AS enrollment_status,
    e.enrolled_at
FROM students       s
JOIN enrollments    e  ON s.student_id    = e.student_id
JOIN course_sections cs ON e.section_id  = cs.section_id
JOIN courses        c  ON cs.course_id   = c.course_id
JOIN semesters      sm ON cs.semester_id = sm.semester_id
LEFT JOIN grades    g  ON e.enrollment_id = g.enrollment_id;

-- ============================================================
-- VIEW 2: v_attendance_summary
-- Attendance % per student per section — covers aggregation
-- ============================================================
CREATE OR REPLACE VIEW v_attendance_summary AS
SELECT
    e.enrollment_id,
    e.student_id,
    e.section_id,
    c.course_name,
    cs.section_code,
    sm.name                                                        AS semester_name,
    COUNT(a.attendance_id)                                         AS total_classes,
    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)         AS classes_attended,
    ROUND(
        SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(a.attendance_id), 0) * 100, 2
    )                                                              AS attendance_percentage
FROM enrollments    e
JOIN course_sections cs ON e.section_id  = cs.section_id
JOIN courses        c  ON cs.course_id   = c.course_id
JOIN semesters      sm ON cs.semester_id = sm.semester_id
LEFT JOIN attendance a  ON e.enrollment_id = a.enrollment_id
GROUP BY e.enrollment_id, e.student_id, e.section_id,
         c.course_name, cs.section_code, sm.name;

-- ============================================================
-- VIEW 3: v_course_roster
-- List of students enrolled in each section — faculty use
-- ============================================================
CREATE OR REPLACE VIEW v_course_roster AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    cs.section_id,
    cs.section_code,
    sm.name                                  AS semester_name,
    CONCAT(f.first_name,' ',f.last_name)     AS faculty_name,
    s.student_id,
    CONCAT(s.first_name,' ',s.last_name)     AS student_name,
    s.email,
    e.enrollment_id,
    e.enrolled_at,
    e.status
FROM course_sections cs
JOIN courses     c  ON cs.course_id   = c.course_id
JOIN semesters   sm ON cs.semester_id = sm.semester_id
JOIN faculty     f  ON cs.faculty_id  = f.faculty_id
JOIN enrollments e  ON cs.section_id  = e.section_id
JOIN students    s  ON e.student_id   = s.student_id
WHERE e.status = 'active';

-- ============================================================
-- VIEW 4: v_admin_enrollment_report
-- Total students enrolled in each section — admin report
-- ============================================================
CREATE OR REPLACE VIEW v_admin_enrollment_report AS
SELECT
    c.course_id,
    c.course_code,
    c.course_name,
    c.credit_hours,
    cs.section_id,
    cs.section_code,
    sm.name                                       AS semester_name,
    CONCAT(f.first_name,' ',f.last_name)          AS faculty_name,
    cs.max_capacity,
    COUNT(e.enrollment_id)                         AS enrolled_count,
    cs.max_capacity - COUNT(e.enrollment_id)       AS seats_remaining,
    ROUND(COUNT(e.enrollment_id)/cs.max_capacity*100, 1) AS fill_percentage
FROM course_sections cs
JOIN courses     c  ON cs.course_id   = c.course_id
JOIN semesters   sm ON cs.semester_id = sm.semester_id
LEFT JOIN faculty     f ON cs.faculty_id = f.faculty_id
LEFT JOIN enrollments e ON cs.section_id  = e.section_id
    AND e.status = 'active'
GROUP BY c.course_id, c.course_code, c.course_name, c.credit_hours,
         cs.section_id, cs.section_code, sm.name,
         f.first_name, f.last_name, cs.max_capacity;

-- ============================================================
-- VIEW 5: v_student_cgpa
-- Computed CGPA per student from completed enrollments with grades
-- Replaces stored students.cgpa column (removed from schema)
-- ============================================================
CREATE OR REPLACE VIEW v_student_cgpa AS
SELECT
    e.student_id,
    ROUND(
        SUM(g.grade_points * c.credit_hours) / NULLIF(SUM(c.credit_hours), 0),
        2
    ) AS cgpa
FROM enrollments     e
JOIN grades          g  ON e.enrollment_id = g.enrollment_id
JOIN course_sections cs ON e.section_id   = cs.section_id
JOIN courses         c  ON cs.course_id   = c.course_id
WHERE e.status = 'completed'
  AND g.grade_points IS NOT NULL
GROUP BY e.student_id;