USE smart_campus;

-- enrollments and grades
DROP PROCEDURE IF EXISTS _seed_enroll;
DELIMITER $$
CREATE PROCEDURE _seed_enroll(
  IN p_sid INT, IN p_sec_id INT, IN p_status VARCHAR(20),
  IN p_marks DECIMAL(5,2), IN p_letter CHAR(2), IN p_points DECIMAL(3,2)
)
BEGIN
  DECLARE v_eid INT;
  INSERT IGNORE INTO enrollments (student_id, section_id, status) VALUES (p_sid, p_sec_id, p_status);
  SET v_eid = LAST_INSERT_ID();
  IF v_eid > 0 THEN
    INSERT IGNORE INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points)
    VALUES (v_eid, p_marks, 100, p_letter, p_points);
  END IF;
END$$
DELIMITER ;

-- get student ids
DROP TEMPORARY TABLE IF EXISTS _sids;
CREATE TEMPORARY TABLE _sids AS SELECT student_id AS sid, program FROM students ORDER BY student_id;

-- get section ids
SET @sp25_cs101a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS101') AND cs.section_code='A');
SET @sp25_cs101b = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS101') AND cs.section_code='B');
SET @sp25_cs205a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='CS205') AND cs.section_code='A');
SET @sp25_mt101a = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='MT101') AND cs.section_code='A');
SET @sp25_bba201 = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='BBA201') AND cs.section_code='A');
SET @sp25_se240  = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='SE240') AND cs.section_code='A');
SET @sp25_it220  = (SELECT section_id FROM course_sections cs JOIN semesters s ON cs.semester_id=s.semester_id WHERE s.name='Spring 2025' AND cs.course_id=(SELECT course_id FROM courses WHERE course_code='IT220') AND cs.section_code='A');

-- enroll students
SET @s1 = (SELECT sid FROM _sids LIMIT 1 OFFSET 0);
SET @s2 = (SELECT sid FROM _sids LIMIT 1 OFFSET 1);
SET @s3 = (SELECT sid FROM _sids LIMIT 1 OFFSET 2);
SET @s4 = (SELECT sid FROM _sids LIMIT 1 OFFSET 3);
SET @s5 = (SELECT sid FROM _sids LIMIT 1 OFFSET 4);
SET @s6 = (SELECT sid FROM _sids LIMIT 1 OFFSET 5);
SET @s7 = (SELECT sid FROM _sids LIMIT 1 OFFSET 6);
SET @s8 = (SELECT sid FROM _sids LIMIT 1 OFFSET 7);
SET @s9 = (SELECT sid FROM _sids LIMIT 1 OFFSET 8);
SET @s10= (SELECT sid FROM _sids LIMIT 1 OFFSET 9);
SET @s11= (SELECT sid FROM _sids LIMIT 1 OFFSET 10);
SET @s12= (SELECT sid FROM _sids LIMIT 1 OFFSET 11);
SET @s13= (SELECT sid FROM _sids LIMIT 1 OFFSET 12);
SET @s14= (SELECT sid FROM _sids LIMIT 1 OFFSET 13);
SET @s15= (SELECT sid FROM _sids LIMIT 1 OFFSET 14);
SET @s16= (SELECT sid FROM _sids LIMIT 1 OFFSET 15);
SET @s17= (SELECT sid FROM _sids LIMIT 1 OFFSET 16);
SET @s18= (SELECT sid FROM _sids LIMIT 1 OFFSET 17);
SET @s19= (SELECT sid FROM _sids LIMIT 1 OFFSET 18);
SET @s20= (SELECT sid FROM _sids LIMIT 1 OFFSET 19);

-- cs101 section a
CALL _seed_enroll(@s1,  @sp25_cs101a, 'completed', 92.00, 'A',  4.00);
CALL _seed_enroll(@s2,  @sp25_cs101a, 'completed', 78.50, 'B',  3.00);
CALL _seed_enroll(@s9,  @sp25_cs101a, 'completed', 85.00, 'A-', 3.70);
CALL _seed_enroll(@s10, @sp25_cs101a, 'completed', 67.00, 'C+', 2.30);
CALL _seed_enroll(@s17, @sp25_cs101a, 'completed', 71.50, 'B-', 2.70);
CALL _seed_enroll(@s18, @sp25_cs101a, 'completed', 90.00, 'A',  4.00);

-- cs101 section b
CALL _seed_enroll(@s4,  @sp25_cs101b, 'completed', 73.00, 'B-', 2.70);
CALL _seed_enroll(@s12, @sp25_cs101b, 'completed', 88.00, 'A-', 3.70);
CALL _seed_enroll(@s20, @sp25_cs101b, 'completed', 62.00, 'C',  2.00);

-- cs205 section a
CALL _seed_enroll(@s1,  @sp25_cs205a, 'completed', 88.00, 'A-', 3.70);
CALL _seed_enroll(@s3,  @sp25_cs205a, 'completed', 75.00, 'B',  3.00);
CALL _seed_enroll(@s9,  @sp25_cs205a, 'completed', 91.00, 'A',  4.00);
CALL _seed_enroll(@s11, @sp25_cs205a, 'completed', 69.00, 'B-', 2.70);

-- mt101 section a
CALL _seed_enroll(@s1,  @sp25_mt101a, 'completed', 80.50, 'B+', 3.30);
CALL _seed_enroll(@s2,  @sp25_mt101a, 'completed', 72.00, 'B-', 2.70);
CALL _seed_enroll(@s5,  @sp25_mt101a, 'completed', 95.00, 'A',  4.00);
CALL _seed_enroll(@s6,  @sp25_mt101a, 'completed', 83.00, 'B+', 3.30);
CALL _seed_enroll(@s13, @sp25_mt101a, 'completed', 77.00, 'B',  3.00);
CALL _seed_enroll(@s14, @sp25_mt101a, 'completed', 56.00, 'F',  0.00);

-- bba201
CALL _seed_enroll(@s7,  @sp25_bba201, 'completed', 82.00, 'B+', 3.30);
CALL _seed_enroll(@s8,  @sp25_bba201, 'completed', 91.50, 'A',  4.00);
CALL _seed_enroll(@s15, @sp25_bba201, 'completed', 68.00, 'C+', 2.30);
CALL _seed_enroll(@s16, @sp25_bba201, 'completed', 74.00, 'B-', 2.70);

-- se240
CALL _seed_enroll(@s5,  @sp25_se240, 'completed', 87.00, 'A-', 3.70);
CALL _seed_enroll(@s6,  @sp25_se240, 'completed', 93.00, 'A',  4.00);
CALL _seed_enroll(@s13, @sp25_se240, 'completed', 79.00, 'B',  3.00);
CALL _seed_enroll(@s14, @sp25_se240, 'completed', 71.00, 'B-', 2.70);

-- it220
CALL _seed_enroll(@s3,  @sp25_it220, 'completed', 86.00, 'A-', 3.70);
CALL _seed_enroll(@s11, @sp25_it220, 'completed', 78.00, 'B',  3.00);
CALL _seed_enroll(@s19, @sp25_it220, 'completed', 65.00, 'C+', 2.30);

-- timetable
SET @fa26 = (SELECT semester_id FROM semesters WHERE name='Fall 2026');

-- cs101 sections
SET @t_cs101a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='CS101') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_cs101b = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='CS101') AND semester_id=@fa26 AND section_code='B' LIMIT 1);
SET @t_cs205a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='CS205') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_cs205b = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='CS205') AND semester_id=@fa26 AND section_code='B' LIMIT 1);
SET @t_cs301a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='CS301') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_mt101a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='MT101') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_bba201a= (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='BBA201') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_bba305a= (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='BBA305') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_se240a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='SE240') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_se315a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='SE315') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_it305a = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='IT305') AND semester_id=@fa26 AND section_code='A' LIMIT 1);
SET @t_it220b = (SELECT section_id FROM course_sections WHERE course_id=(SELECT course_id FROM courses WHERE course_code='IT220') AND semester_id=@fa26 AND section_code='B' LIMIT 1);

INSERT IGNORE INTO timetable_slots (section_id, day_of_week, start_time, end_time, room) VALUES
-- cs101 a
(@t_cs101a, 'Mon', '09:00:00', '10:15:00', 'Room 101'),
(@t_cs101a, 'Wed', '09:00:00', '10:15:00', 'Room 101'),
-- cs101 b
(@t_cs101b, 'Tue', '09:00:00', '10:15:00', 'Room 102'),
(@t_cs101b, 'Thu', '09:00:00', '10:15:00', 'Room 102'),
-- cs205 a
(@t_cs205a, 'Mon', '10:30:00', '11:45:00', 'Lab 201'),
(@t_cs205a, 'Wed', '10:30:00', '11:45:00', 'Lab 201'),
-- cs205 b
(@t_cs205b, 'Tue', '10:30:00', '11:45:00', 'Lab 202'),
(@t_cs205b, 'Thu', '10:30:00', '11:45:00', 'Lab 202'),
-- cs301 a
(@t_cs301a, 'Mon', '12:00:00', '12:50:00', 'Room 301'),
(@t_cs301a, 'Wed', '12:00:00', '12:50:00', 'Room 301'),
(@t_cs301a, 'Fri', '12:00:00', '12:50:00', 'Room 301'),
-- mt101
(@t_mt101a, 'Tue', '12:00:00', '13:15:00', 'Room 105'),
(@t_mt101a, 'Thu', '12:00:00', '13:15:00', 'Room 105'),
-- bba201
(@t_bba201a,'Mon', '14:00:00', '15:15:00', 'Room 401'),
(@t_bba201a,'Wed', '14:00:00', '15:15:00', 'Room 401'),
-- bba305
(@t_bba305a,'Tue', '14:00:00', '15:15:00', 'Room 402'),
(@t_bba305a,'Thu', '14:00:00', '15:15:00', 'Room 402'),
-- se240
(@t_se240a, 'Mon', '15:30:00', '16:45:00', 'Lab 301'),
(@t_se240a, 'Wed', '15:30:00', '16:45:00', 'Lab 301'),
-- se315
(@t_se315a, 'Tue', '15:30:00', '16:45:00', 'Lab 302'),
(@t_se315a, 'Thu', '15:30:00', '16:45:00', 'Lab 302'),
-- it305
(@t_it305a, 'Mon', '10:30:00', '11:45:00', 'Room 203'),
(@t_it305a, 'Fri', '10:30:00', '11:45:00', 'Room 203'),
-- it220 b
(@t_it220b, 'Wed', '14:00:00', '15:15:00', 'Lab 203'),
(@t_it220b, 'Fri', '14:00:00', '15:15:00', 'Lab 203');

CALL _seed_enroll(@s1,  @t_cs301a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s2,  @t_cs301a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s9,  @t_cs301a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s10, @t_cs205b, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s17, @t_cs205b, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s18, @t_cs301a, 'active', NULL, NULL, NULL);

-- it students
CALL _seed_enroll(@s3,  @t_it305a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s11, @t_it305a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s4,  @t_it220b, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s12, @t_it220b, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s19, @t_it305a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s20, @t_it220b, 'active', NULL, NULL, NULL);

-- se students
CALL _seed_enroll(@s5,  @t_se240a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s6,  @t_se315a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s13, @t_se240a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s14, @t_se315a, 'active', NULL, NULL, NULL);

-- bba students
CALL _seed_enroll(@s7,  @t_bba305a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s8,  @t_bba201a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s15, @t_bba305a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s16, @t_bba201a, 'active', NULL, NULL, NULL);

-- more students
SET @s21= (SELECT sid FROM _sids LIMIT 1 OFFSET 20);
SET @s22= (SELECT sid FROM _sids LIMIT 1 OFFSET 21);
SET @s23= (SELECT sid FROM _sids LIMIT 1 OFFSET 22);
SET @s24= (SELECT sid FROM _sids LIMIT 1 OFFSET 23);
SET @s25= (SELECT sid FROM _sids LIMIT 1 OFFSET 24);
SET @s26= (SELECT sid FROM _sids LIMIT 1 OFFSET 25);
SET @s27= (SELECT sid FROM _sids LIMIT 1 OFFSET 26);
SET @s28= (SELECT sid FROM _sids LIMIT 1 OFFSET 27);
SET @s29= (SELECT sid FROM _sids LIMIT 1 OFFSET 28);
SET @s30= (SELECT sid FROM _sids LIMIT 1 OFFSET 29);

CALL _seed_enroll(@s21, @t_se240a,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s22, @t_se315a,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s23, @t_bba305a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s24, @t_bba201a, 'active', NULL, NULL, NULL);
CALL _seed_enroll(@s25, @t_cs101a,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s26, @t_cs101b,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s27, @t_it305a,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s28, @t_it220b,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s29, @t_se240a,  'active', NULL, NULL, NULL);
CALL _seed_enroll(@s30, @t_mt101a,  'active', NULL, NULL, NULL);

-- cleanup helper
DROP PROCEDURE IF EXISTS _seed_enroll;
DROP TEMPORARY TABLE IF EXISTS _sids;
