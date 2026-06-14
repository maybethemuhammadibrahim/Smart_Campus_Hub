USE smart_campus;

-- semesters
INSERT IGNORE INTO semesters (name, start_date, end_date, is_active) VALUES
('Spring 2025', '2025-01-15', '2025-05-31', 0),
('Summer 2025', '2025-06-01', '2025-08-15', 0),
('Fall 2025',   '2025-08-20', '2025-12-20', 0);

-- faculty
INSERT INTO users (username, password, role, is_active) VALUES
('f_ahmed',   '1234', 'faculty', 1),
('f_farooq',  '1234', 'faculty', 1),
('f_yasmin',  '1234', 'faculty', 1),
('f_qureshi', '1234', 'faculty', 1);

SET @uid_ahmed   = LAST_INSERT_ID();
SET @uid_farooq  = @uid_ahmed + 1;
SET @uid_yasmin  = @uid_ahmed + 2;
SET @uid_qureshi = @uid_ahmed + 3;

INSERT INTO faculty (user_id, first_name, last_name, email, department, designation) VALUES
(@uid_ahmed,   'Tariq',  'Ahmed',   'tariq.ahmed@campus.edu',   'Mathematics',          'Professor'),
(@uid_farooq,  'Saad',   'Farooq',  'saad.farooq@campus.edu',  'Computer Science',     'Lecturer'),
(@uid_yasmin,  'Ayesha', 'Yasmin',  'ayesha.yasmin@campus.edu', 'Business School',      'Assistant Professor'),
(@uid_qureshi, 'Imran',  'Qureshi', 'imran.qureshi@campus.edu','Software Engineering', 'Associate Professor');

-- courses
INSERT IGNORE INTO courses (course_code, course_name, credit_hours) VALUES
('CS301', 'Data Structures and Algorithms', 3),
('CS310', 'Operating Systems', 3),
('MT101', 'Calculus I', 3),
('MT201', 'Linear Algebra', 3),
('IT305', 'Network Security', 3),
('SE410', 'DevOps and CI/CD', 3);

-- students
INSERT INTO users (username, password, role, is_active) VALUES
('s_ali01','1234','student',1),('s_zara02','1234','student',1),
('s_ahmed03','1234','student',1),('s_sana04','1234','student',1),
('s_bilal05','1234','student',1),('s_nadia06','1234','student',1),
('s_omar07','1234','student',1),('s_hira08','1234','student',1),
('s_faisal09','1234','student',1),('s_amina10','1234','student',1),
('s_imran11','1234','student',1),('s_rabia12','1234','student',1),
('s_kamran13','1234','student',1),('s_saima14','1234','student',1),
('s_asad15','1234','student',1),('s_noor16','1234','student',1),
('s_waqas17','1234','student',1),('s_mehak18','1234','student',1),
('s_danish19','1234','student',1),('s_farah20','1234','student',1),
('s_junaid21','1234','student',1),('s_anam22','1234','student',1),
('s_rashid23','1234','student',1),('s_bushra24','1234','student',1),
('s_shahid25','1234','student',1),('s_uzma26','1234','student',1),
('s_adnan27','1234','student',1),('s_sidra28','1234','student',1),
('s_nabeel29','1234','student',1),('s_maria30','1234','student',1),
('s_taha31','1234','student',1),('s_kiran32','1234','student',1),
('s_shoaib33','1234','student',1),('s_lubna34','1234','student',1),
('s_hamid35','1234','student',1),('s_aliya36','1234','student',1),
('s_yasir37','1234','student',1),('s_sadia38','1234','student',1),
('s_rizwan39','1234','student',1),('s_tahira40','1234','student',1),
('s_kashif41','1234','student',1),('s_anum42','1234','student',1),
('s_sajid43','1234','student',1);

SET @s_base = LAST_INSERT_ID();

INSERT INTO students (user_id, first_name, last_name, email, dob, program, batch_year) VALUES
(@s_base+0,  'Ali',     'Raza',     'ali.raza@student.edu',     '2002-03-15', 'BS Computer Science', 2022),
(@s_base+1,  'Zara',    'Khan',     'zara.khan@student.edu',    '2003-07-22', 'BS Computer Science', 2023),
(@s_base+2,  'Ahmed',   'Shah',     'ahmed.shah@student.edu',   '2001-11-10', 'BS Information Technology', 2021),
(@s_base+3,  'Sana',    'Malik',    'sana.malik@student.edu',   '2002-05-18', 'BS Information Technology', 2022),
(@s_base+4,  'Bilal',   'Hussain',  'bilal.hussain@student.edu','2003-01-25', 'BS Software Engineering', 2023),
(@s_base+5,  'Nadia',   'Akhtar',   'nadia.akhtar@student.edu', '2002-09-30', 'BS Software Engineering', 2022),
(@s_base+6,  'Omar',    'Farooqi',  'omar.farooqi@student.edu', '2001-04-12', 'BBA', 2021),
(@s_base+7,  'Hira',    'Batool',   'hira.batool@student.edu',  '2003-08-05', 'BBA', 2023),
(@s_base+8,  'Faisal',  'Javed',    'faisal.javed@student.edu', '2002-02-28', 'BS Computer Science', 2022),
(@s_base+9,  'Amina',   'Tariq',    'amina.tariq@student.edu',  '2003-06-14', 'BS Computer Science', 2023),
(@s_base+10, 'Imran',   'Aslam',    'imran.aslam@student.edu',  '2001-12-03', 'BS Information Technology', 2021),
(@s_base+11, 'Rabia',   'Nawaz',    'rabia.nawaz@student.edu',  '2002-10-20', 'BS Information Technology', 2022),
(@s_base+12, 'Kamran',  'Younus',   'kamran.younus@student.edu','2003-03-08', 'BS Software Engineering', 2023),
(@s_base+13, 'Saima',   'Pervez',   'saima.pervez@student.edu', '2002-07-11', 'BS Software Engineering', 2022),
(@s_base+14, 'Asad',    'Mehmood',  'asad.mehmood@student.edu', '2001-01-19', 'BBA', 2021),
(@s_base+15, 'Noor',    'Fatima',   'noor.fatima2@student.edu', '2003-05-27', 'BBA', 2023),
(@s_base+16, 'Waqas',   'Aziz',     'waqas.aziz@student.edu',   '2002-08-15', 'BS Computer Science', 2022),
(@s_base+17, 'Mehak',   'Zahoor',   'mehak.zahoor@student.edu', '2003-11-02', 'BS Computer Science', 2023),
(@s_base+18, 'Danish',  'Rafiq',    'danish.rafiq@student.edu', '2001-06-23', 'BS Information Technology', 2021),
(@s_base+19, 'Farah',   'Sultana',  'farah.sultana@student.edu','2002-04-09', 'BS Information Technology', 2022),
(@s_base+20, 'Junaid',  'Anwar',    'junaid.anwar@student.edu', '2003-09-17', 'BS Software Engineering', 2023),
(@s_base+21, 'Anam',    'Riaz',     'anam.riaz@student.edu',    '2002-01-30', 'BS Software Engineering', 2022),
(@s_base+22, 'Rashid',  'Munir',    'rashid.munir@student.edu', '2001-10-14', 'BBA', 2021),
(@s_base+23, 'Bushra',  'Hameed',   'bushra.hameed@student.edu','2003-02-06', 'BBA', 2023),
(@s_base+24, 'Shahid',  'Latif',    'shahid.latif@student.edu', '2002-12-25', 'BS Computer Science', 2022),
(@s_base+25, 'Uzma',    'Ghani',    'uzma.ghani@student.edu',   '2003-04-18', 'BS Computer Science', 2023),
(@s_base+26, 'Adnan',   'Saeed',    'adnan.saeed@student.edu',  '2001-08-07', 'BS Information Technology', 2021),
(@s_base+27, 'Sidra',   'Wahab',    'sidra.wahab@student.edu',  '2002-06-12', 'BS Information Technology', 2022),
(@s_base+28, 'Nabeel',  'Zafar',    'nabeel.zafar@student.edu', '2003-10-30', 'BS Software Engineering', 2023),
(@s_base+29, 'Maria',   'Akram',    'maria.akram@student.edu',  '2002-03-21', 'BS Software Engineering', 2022),
(@s_base+30, 'Taha',    'Bukhari',  'taha.bukhari@student.edu', '2001-07-16', 'BBA', 2021),
(@s_base+31, 'Kiran',   'Qadir',    'kiran.qadir@student.edu',  '2003-12-09', 'BBA', 2023),
(@s_base+32, 'Shoaib',  'Nasir',    'shoaib.nasir@student.edu', '2002-05-04', 'BS Computer Science', 2022),
(@s_base+33, 'Lubna',   'Haider',   'lubna.haider@student.edu', '2003-01-13', 'BS Computer Science', 2023),
(@s_base+34, 'Hamid',   'Abbasi',   'hamid.abbasi@student.edu', '2001-09-28', 'BS Information Technology', 2021),
(@s_base+35, 'Aliya',   'Siddiqui', 'aliya.siddiqui@student.edu','2002-11-15','BS Information Technology', 2022),
(@s_base+36, 'Yasir',   'Rana',     'yasir.rana@student.edu',   '2003-06-01', 'BS Software Engineering', 2023),
(@s_base+37, 'Sadia',   'Bibi',     'sadia.bibi@student.edu',  '2002-02-14', 'BS Software Engineering', 2022),
(@s_base+38, 'Rizwan',  'Chaudhry', 'rizwan.ch@student.edu',   '2001-04-22', 'BBA', 2021),
(@s_base+39, 'Tahira',  'Naz',      'tahira.naz@student.edu',  '2003-08-19', 'BBA', 2023),
(@s_base+40, 'Kashif',  'Manzoor',  'kashif.manzoor@student.edu','2002-10-07','BS Computer Science', 2022),
(@s_base+41, 'Anum',    'Rasheed',  'anum.rasheed@student.edu', '2003-03-26', 'BS Computer Science', 2023),
(@s_base+42, 'Sajid',   'Mahmood',  'sajid.mahmood@student.edu','2001-11-11','BS Information Technology', 2021);
