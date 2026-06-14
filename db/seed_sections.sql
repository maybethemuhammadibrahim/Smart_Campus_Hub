USE smart_campus;

SET @sem_sp25 = (SELECT semester_id FROM semesters WHERE name='Spring 2025');
SET @sem_su25 = (SELECT semester_id FROM semesters WHERE name='Summer 2025');
SET @sem_fa25 = (SELECT semester_id FROM semesters WHERE name='Fall 2025');
SET @sem_fa26 = (SELECT semester_id FROM semesters WHERE name='Fall 2026');

SET @f_khan    = (SELECT faculty_id FROM faculty WHERE last_name='Khan' AND department='Computer Science' LIMIT 1);
SET @f_mehmood = (SELECT faculty_id FROM faculty WHERE last_name='Mehmood' LIMIT 1);
SET @f_rizvi   = (SELECT faculty_id FROM faculty WHERE last_name='Rizvi' LIMIT 1);
SET @f_nadeem  = (SELECT faculty_id FROM faculty WHERE last_name='Nadeem' LIMIT 1);
SET @f_ahmed   = (SELECT faculty_id FROM faculty WHERE last_name='Ahmed' AND first_name='Tariq' LIMIT 1);
SET @f_farooq  = (SELECT faculty_id FROM faculty WHERE last_name='Farooq' LIMIT 1);
SET @f_yasmin  = (SELECT faculty_id FROM faculty WHERE last_name='Yasmin' LIMIT 1);
SET @f_qureshi = (SELECT faculty_id FROM faculty WHERE last_name='Qureshi' AND first_name='Imran' LIMIT 1);

SET @c_cs101 = (SELECT course_id FROM courses WHERE course_code='CS101');
SET @c_cs205 = (SELECT course_id FROM courses WHERE course_code='CS205');
SET @c_it220 = (SELECT course_id FROM courses WHERE course_code='IT220');
SET @c_is310 = (SELECT course_id FROM courses WHERE course_code='IS310');
SET @c_bba201= (SELECT course_id FROM courses WHERE course_code='BBA201');
SET @c_bba305= (SELECT course_id FROM courses WHERE course_code='BBA305');
SET @c_se240 = (SELECT course_id FROM courses WHERE course_code='SE240');
SET @c_se315 = (SELECT course_id FROM courses WHERE course_code='SE315');
SET @c_cs301 = (SELECT course_id FROM courses WHERE course_code='CS301');
SET @c_cs310 = (SELECT course_id FROM courses WHERE course_code='CS310');
SET @c_mt101 = (SELECT course_id FROM courses WHERE course_code='MT101');
SET @c_mt201 = (SELECT course_id FROM courses WHERE course_code='MT201');
SET @c_it305 = (SELECT course_id FROM courses WHERE course_code='IT305');
SET @c_se410 = (SELECT course_id FROM courses WHERE course_code='SE410');

INSERT IGNORE INTO course_sections (course_id, semester_id, faculty_id, section_code, max_capacity) VALUES
(@c_cs101, @sem_sp25, @f_khan,    'A', 40),
(@c_cs101, @sem_sp25, @f_farooq,  'B', 40),
(@c_cs205, @sem_sp25, @f_mehmood, 'A', 35),
(@c_mt101, @sem_sp25, @f_ahmed,   'A', 45),
(@c_mt101, @sem_sp25, @f_ahmed,   'B', 45),
(@c_bba201,@sem_sp25, @f_rizvi,   'A', 40),
(@c_se240, @sem_sp25, @f_nadeem,  'A', 35),
(@c_it220, @sem_sp25, @f_mehmood, 'A', 35);

INSERT IGNORE INTO course_sections (course_id, semester_id, faculty_id, section_code, max_capacity) VALUES
(@c_cs301, @sem_fa25, @f_khan,    'A', 40),
(@c_cs301, @sem_fa25, @f_farooq,  'B', 40),
(@c_cs310, @sem_fa25, @f_farooq,  'A', 35),
(@c_cs205, @sem_fa25, @f_mehmood, 'A', 35),
(@c_cs205, @sem_fa25, @f_khan,    'B', 35),
(@c_mt201, @sem_fa25, @f_ahmed,   'A', 45),
(@c_bba305,@sem_fa25, @f_yasmin,  'A', 40),
(@c_bba305,@sem_fa25, @f_rizvi,   'B', 40),
(@c_se315, @sem_fa25, @f_qureshi, 'A', 35),
(@c_it305, @sem_fa25, @f_mehmood, 'A', 35),
(@c_se410, @sem_fa25, @f_nadeem,  'A', 30);

INSERT IGNORE INTO course_sections (course_id, semester_id, faculty_id, section_code, max_capacity) VALUES
(@c_cs101, @sem_fa26, @f_farooq,  'B', 40),
(@c_cs101, @sem_fa26, @f_ahmed,   'C', 40),
(@c_cs205, @sem_fa26, @f_khan,    'B', 35),
(@c_cs301, @sem_fa26, @f_khan,    'A', 40),
(@c_cs301, @sem_fa26, @f_farooq,  'B', 40),
(@c_mt101, @sem_fa26, @f_ahmed,   'A', 45),
(@c_mt201, @sem_fa26, @f_ahmed,   'A', 45),
(@c_bba201,@sem_fa26, @f_yasmin,  'A', 40),
(@c_bba305,@sem_fa26, @f_rizvi,   'A', 40),
(@c_se240, @sem_fa26, @f_qureshi, 'A', 35),
(@c_se315, @sem_fa26, @f_nadeem,  'A', 35),
(@c_se410, @sem_fa26, @f_qureshi, 'A', 30),
(@c_it305, @sem_fa26, @f_mehmood, 'A', 35),
(@c_it220, @sem_fa26, @f_mehmood, 'B', 35);
