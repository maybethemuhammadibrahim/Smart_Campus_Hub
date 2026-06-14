USE smart_campus;

-- remove wrong bba enrollment
DELETE FROM grades WHERE enrollment_id IN (
  SELECT enrollment_id FROM enrollments WHERE student_id=10 AND section_id=5
);
DELETE FROM enrollments WHERE student_id=10 AND section_id=5;
DELETE FROM grades WHERE enrollment_id IN (
  SELECT enrollment_id FROM enrollments WHERE student_id=10 AND section_id=19
);
DELETE FROM enrollments WHERE student_id=10 AND section_id=19;

-- alis fall 2025 completed courses
SET @fa25_cs301a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS301') AND cs.section_code='A');
SET @fa25_cs205b = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS205') AND cs.section_code='B');
SET @fa25_cs310a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS310') AND cs.section_code='A');
SET @fa25_mt201a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='MT201') AND cs.section_code='A');

-- fall 2025 completed enrollments
INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa25_cs301a, 'completed');
SET @e1 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points) VALUES (@e1, 91.00, 100, 'A', 4.00);

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa25_cs205b, 'completed');
SET @e2 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points) VALUES (@e2, 85.50, 100, 'A-', 3.70);

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa25_cs310a, 'completed');
SET @e3 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points) VALUES (@e3, 78.00, 100, 'B', 3.00);

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa25_mt201a, 'completed');
SET @e4 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points) VALUES (@e4, 82.00, 100, 'B+', 3.30);


SET @fa26_cs301a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2026' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS301') AND cs.section_code='A');
SET @fa26_cs205b = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2026' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS205') AND cs.section_code='B');
SET @fa26_cs101a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2026' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS101') AND cs.section_code='A');
SET @fa26_mt101a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2026' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='MT101') AND cs.section_code='A');
SET @fa26_se240a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Fall 2026' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='SE240') AND cs.section_code='A');

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa26_cs301a, 'active');
SET @ae1 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id) VALUES (@ae1);

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa26_cs205b, 'active');
SET @ae2 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id) VALUES (@ae2);

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa26_cs101a, 'active');
SET @ae3 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id) VALUES (@ae3);

INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (10, @fa26_mt101a, 'active');
SET @ae4 = LAST_INSERT_ID();
INSERT IGNORE INTO grades (enrollment_id) VALUES (@ae4);


SET @ali_uid = (SELECT user_id FROM students WHERE student_id=10);
SET @khan_uid= (SELECT user_id FROM faculty WHERE faculty_id=1);

INSERT IGNORE INTO attendance (enrollment_id, class_date, status, marked_by) VALUES
(@ae1, '2026-01-05', 'present', @khan_uid),
(@ae1, '2026-01-07', 'present', @khan_uid),
(@ae1, '2026-01-09', 'present', @khan_uid),
(@ae1, '2026-01-12', 'present', @khan_uid),
(@ae1, '2026-01-14', 'late',    @khan_uid),
(@ae1, '2026-01-16', 'present', @khan_uid),
(@ae1, '2026-01-19', 'present', @khan_uid),
(@ae1, '2026-01-21', 'absent',  @khan_uid),
(@ae1, '2026-01-23', 'present', @khan_uid),
(@ae1, '2026-01-26', 'present', @khan_uid),
(@ae1, '2026-01-28', 'present', @khan_uid),
(@ae1, '2026-01-30', 'present', @khan_uid),
(@ae1, '2026-02-02', 'present', @khan_uid),
(@ae1, '2026-02-04', 'late',    @khan_uid),
(@ae1, '2026-02-06', 'present', @khan_uid);


INSERT IGNORE INTO attendance (enrollment_id, class_date, status, marked_by) VALUES
(@ae2, '2026-01-06', 'present', @khan_uid),
(@ae2, '2026-01-08', 'present', @khan_uid),
(@ae2, '2026-01-13', 'present', @khan_uid),
(@ae2, '2026-01-15', 'absent',  @khan_uid),
(@ae2, '2026-01-20', 'present', @khan_uid),
(@ae2, '2026-01-22', 'present', @khan_uid),
(@ae2, '2026-01-27', 'present', @khan_uid),
(@ae2, '2026-01-29', 'present', @khan_uid),
(@ae2, '2026-02-03', 'present', @khan_uid),
(@ae2, '2026-02-05', 'present', @khan_uid);


INSERT IGNORE INTO attendance (enrollment_id, class_date, status, marked_by) VALUES
(@ae3, '2026-01-05', 'present', @khan_uid),
(@ae3, '2026-01-07', 'present', @khan_uid),
(@ae3, '2026-01-12', 'present', @khan_uid),
(@ae3, '2026-01-14', 'present', @khan_uid),
(@ae3, '2026-01-19', 'late',    @khan_uid),
(@ae3, '2026-01-21', 'present', @khan_uid),
(@ae3, '2026-01-26', 'present', @khan_uid),
(@ae3, '2026-01-28', 'present', @khan_uid);


INSERT IGNORE INTO attendance (enrollment_id, class_date, status, marked_by)
SELECT e.enrollment_id, d.dt, 
  ELT(1 + FLOOR(RAND(e.enrollment_id * 100 + d.n) * 10), 
    'present','present','present','present','present','present','present','present','late','absent'),
  @khan_uid
FROM enrollments e
JOIN (
  SELECT '2026-01-05' AS dt, 1 AS n UNION SELECT '2026-01-07',2 UNION SELECT '2026-01-09',3
  UNION SELECT '2026-01-12',4 UNION SELECT '2026-01-14',5 UNION SELECT '2026-01-16',6
  UNION SELECT '2026-01-19',7 UNION SELECT '2026-01-21',8 UNION SELECT '2026-01-23',9
  UNION SELECT '2026-01-26',10 UNION SELECT '2026-01-28',11 UNION SELECT '2026-01-30',12
) d ON 1=1
WHERE e.section_id = @fa26_cs301a AND e.status='active' AND e.student_id != 10;
