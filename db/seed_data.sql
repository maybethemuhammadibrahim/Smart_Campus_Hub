-- ============================================================
-- Smart Campus Academic Management System — Seed Data
-- Sample data with up to 10 rows per table
-- ============================================================

USE smart_campus;

-- Optional cleanup for repeatable runs
DELETE FROM attendance;
DELETE FROM grades;
DELETE FROM enrollments;
DELETE FROM courses;
DELETE FROM faculty;
DELETE FROM students;
DELETE FROM users;

-- Reset auto-increment counters
ALTER TABLE users AUTO_INCREMENT = 1;
ALTER TABLE students AUTO_INCREMENT = 1;
ALTER TABLE faculty AUTO_INCREMENT = 1;
ALTER TABLE courses AUTO_INCREMENT = 1;
ALTER TABLE enrollments AUTO_INCREMENT = 1;
ALTER TABLE attendance AUTO_INCREMENT = 1;
ALTER TABLE grades AUTO_INCREMENT = 1;

-- ============================================================
-- users (10 rows)
-- Note: password values are demo bcrypt-style hashes
-- ============================================================
INSERT INTO users (user_id, username, password, role, is_active) VALUES
(1,  'admin_ali',      '$2b$12$X7j3wqA1x1L2Y8N0mQeR1uJkD4h6p9s2t5v8w0y3z6A9bC1dE2fG', 'admin',   TRUE),
(2,  'admin_sara',     '$2b$12$Q1w2e3r4t5y6u7i8o9p0aSDFGHJKLZXCVBNMqwertyuiopasdfgh', 'admin',   TRUE),
(3,  'f_khan',         '$2b$12$hG4kP1aQ9mN8vC7xZ6lT5rE3wS2dF1gH0jK9lP8oI7uY6tR5eW4q', 'faculty', TRUE),
(4,  'f_mehmood',      '$2b$12$jD3sA7pL0qW9eR4tY6uI8oP2aS5dF7gH1jK3lZ6xC9vB2nM4qW8r', 'faculty', TRUE),
(5,  'f_rizvi',        '$2b$12$kL9pO4iU1yT8rE6wQ3aS7dF2gH5jK0lZ4xC8vB1nM6qW9eR3tY7u', 'faculty', TRUE),
(6,  'f_nadeem',       '$2b$12$mN2bV6cX9zA1sD4fG7hJ0kL3pO8iU5yT2rE6wQ9aS3dF7gH1jK4l', 'faculty', TRUE),
(7,  's_hassan',       '$2b$12$nB7vC3xZ0aS5dF9gH2jK6lP1oI4uY8tR3eW7qA2sD6fG0hJ5kL9p', 'student', TRUE),
(8,  's_fatima',       '$2b$12$pO1iU5yT9rE2wQ6aS0dF4gH8jK3lZ7xC1vB5nM9qW2eR6tY0uI4o', 'student', TRUE),
(9,  's_usman',        '$2b$12$qW8eR3tY7uI1oP5aS9dF2gH6jK0lZ4xC8vB2nM6qW1eR5tY9uI3o', 'student', TRUE),
(10, 's_maryam',       '$2b$12$rT4yU8iO2pA6sD0fG5hJ9kL3zX7cV1bN4mQ8wE2rT6yU0iO5pA9s', 'student', TRUE);

-- ============================================================
-- students (4 rows)
-- ============================================================
INSERT INTO students (student_id, user_id, first_name, last_name, email, dob, program, batch_year, cgpa) VALUES
(1, 7,  'Hassan', 'Raza',   'hassan.raza@student.smartcampus.edu',  '2004-03-14', 'BS Computer Science',        2022, 3.42),
(2, 8,  'Fatima', 'Noor',   'fatima.noor@student.smartcampus.edu',  '2003-11-22', 'BS Information Technology',   2021, 3.76),
(3, 9,  'Usman',  'Iqbal',  'usman.iqbal@student.smartcampus.edu',  '2004-07-09', 'BBA',                         2022, 3.18),
(4, 10, 'Maryam', 'Saleem', 'maryam.saleem@student.smartcampus.edu', '2005-01-30', 'BS Software Engineering',     2023, 3.91);

-- ============================================================
-- faculty (4 rows)
-- ============================================================
INSERT INTO faculty (faculty_id, user_id, first_name, last_name, email, department, designation) VALUES
(1, 3, 'Adeel',   'Khan',    'adeel.khan@smartcampus.edu',   'Computer Science',    'Assistant Professor'),
(2, 4, 'Hina',    'Mehmood', 'hina.mehmood@smartcampus.edu', 'Information Systems', 'Lecturer'),
(3, 5, 'Bilal',   'Rizvi',   'bilal.rizvi@smartcampus.edu',  'Business School',     'Associate Professor'),
(4, 6, 'Samina',  'Nadeem',  'samina.nadeem@smartcampus.edu','Software Engineering','Assistant Professor');

-- ============================================================
-- courses (8 rows)
-- ============================================================
INSERT INTO courses (course_id, course_code, course_name, credit_hours, semester, faculty_id, max_capacity) VALUES
(1, 'CS101',   'Introduction to Programming',      3, 'Fall 2026',   1, 50),
(2, 'CS205',   'Database Systems',                 3, 'Fall 2026',   1, 45),
(3, 'IT220',   'Web Application Development',      3, 'Fall 2026',   2, 40),
(4, 'IS310',   'Management Information Systems',   3, 'Fall 2026',   2, 35),
(5, 'BBA201',  'Principles of Marketing',          3, 'Fall 2026',   3, 60),
(6, 'BBA305',  'Business Analytics',               3, 'Fall 2026',   3, 40),
(7, 'SE240',   'Software Design and Architecture', 3, 'Fall 2026',   4, 40),
(8, 'SE315',   'Software Quality Assurance',       3, 'Fall 2026',   4, 35);

-- ============================================================
-- enrollments (10 rows)
-- ============================================================
INSERT INTO enrollments (enrollment_id, student_id, course_id, enrolled_at, status) VALUES
(1,  1, 1, '2026-08-20 09:10:00', 'active'),
(2,  1, 2, '2026-08-20 09:12:00', 'active'),
(3,  1, 3, '2026-08-20 09:14:00', 'active'),
(4,  2, 2, '2026-08-21 10:00:00', 'active'),
(5,  2, 4, '2026-08-21 10:02:00', 'active'),
(6,  2, 7, '2026-08-21 10:04:00', 'active'),
(7,  3, 5, '2026-08-22 11:20:00', 'active'),
(8,  3, 6, '2026-08-22 11:22:00', 'completed'),
(9,  4, 1, '2026-08-23 12:00:00', 'active'),
(10, 4, 8, '2026-08-23 12:02:00', 'active');

-- ============================================================
-- attendance (10 rows)
-- marked_by stores faculty user_id
-- ============================================================
INSERT INTO attendance (attendance_id, enrollment_id, class_date, status, marked_by) VALUES
(1,  1,  '2026-09-01', 'present', 3),
(2,  2,  '2026-09-01', 'present', 3),
(3,  3,  '2026-09-01', 'late',    4),
(4,  4,  '2026-09-02', 'present', 3),
(5,  5,  '2026-09-02', 'absent',  4),
(6,  6,  '2026-09-02', 'present', 6),
(7,  7,  '2026-09-03', 'present', 5),
(8,  8,  '2026-09-03', 'present', 5),
(9,  9,  '2026-09-04', 'late',    3),
(10, 10, '2026-09-04', 'present', 6);

-- ============================================================
-- grades (10 rows)
-- One row per enrollment
-- ============================================================
INSERT INTO grades (grade_id, enrollment_id, marks_obtained, total_marks, letter_grade, grade_points) VALUES
(1,  1,  86.50, 100.00, 'A',  4.00),
(2,  2,  79.00, 100.00, 'B+', 3.33),
(3,  3,  74.00, 100.00, 'B',  3.00),
(4,  4,  91.00, 100.00, 'A',  4.00),
(5,  5,  83.00, 100.00, 'A-', 3.67),
(6,  6,  88.50, 100.00, 'A',  4.00),
(7,  7,  72.00, 100.00, 'B',  3.00),
(8,  8,  69.00, 100.00, 'C+', 2.33),
(9,  9,  94.00, 100.00, 'A',  4.00),
(10, 10, 81.00, 100.00, 'A-', 3.67);

