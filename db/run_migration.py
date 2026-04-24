"""Run the database migration to add section support and fix triggers."""
import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1', port=3306, user='root', password='1234', database='smart_campus'
)
cursor = conn.cursor()

steps = []

# Step 1: Check if section column already exists
cursor.execute("SHOW COLUMNS FROM courses LIKE 'section'")
if cursor.fetchone():
    print("⚠️  'section' column already exists — skipping ALTER TABLE")
else:
    cursor.execute("ALTER TABLE courses ADD COLUMN section VARCHAR(10) NOT NULL DEFAULT 'A' AFTER semester")
    conn.commit()
    steps.append("✅ Added 'section' column to courses")

# Step 2: Drop old unique index on course_code (if exists)
cursor.execute("SHOW INDEX FROM courses WHERE Key_name = 'course_code'")
if cursor.fetchone():
    cursor.execute("ALTER TABLE courses DROP INDEX course_code")
    conn.commit()
    steps.append("✅ Dropped old unique index on course_code")

# Step 3: Add new unique constraint (if not exists)
cursor.execute("SHOW INDEX FROM courses WHERE Key_name = 'uq_course_section'")
if cursor.fetchone():
    print("⚠️  uq_course_section index already exists — skipping")
else:
    cursor.execute("ALTER TABLE courses ADD CONSTRAINT uq_course_section UNIQUE (course_code, section, semester)")
    conn.commit()
    steps.append("✅ Added unique constraint (course_code, section, semester)")

# Step 4: Add section index
cursor.execute("SHOW INDEX FROM courses WHERE Key_name = 'idx_courses_section'")
if cursor.fetchone():
    print("⚠️  idx_courses_section index already exists — skipping")
else:
    cursor.execute("CREATE INDEX idx_courses_section ON courses(course_code, section)")
    conn.commit()
    steps.append("✅ Added index idx_courses_section")

# Step 5: Drop the broken AFTER UPDATE trigger
cursor.execute("DROP TRIGGER IF EXISTS trg_grade_after_update")
conn.commit()
steps.append("✅ Dropped broken trg_grade_after_update trigger")

# Step 6: Drop old BEFORE UPDATE trigger (we'll replace it)
cursor.execute("DROP TRIGGER IF EXISTS trg_grade_before_update")
conn.commit()
steps.append("✅ Dropped old trg_grade_before_update trigger")

# Step 7: Create fixed BEFORE UPDATE trigger (validation + auto letter grade)
cursor.execute("""
CREATE TRIGGER trg_grade_before_update
BEFORE UPDATE ON grades
FOR EACH ROW
BEGIN
    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL THEN
        IF NEW.marks_obtained < 0 OR NEW.marks_obtained > NEW.total_marks THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'marks_obtained must be between 0 and total_marks';
        END IF;
    END IF;

    IF NEW.marks_obtained IS NOT NULL AND NEW.total_marks IS NOT NULL
       AND NEW.total_marks > 0 THEN
        SET @v_pct = (NEW.marks_obtained / NEW.total_marks) * 100;
        IF    @v_pct >= 90 THEN SET NEW.letter_grade='A',  NEW.grade_points=4.00;
        ELSEIF @v_pct >= 85 THEN SET NEW.letter_grade='A-', NEW.grade_points=3.70;
        ELSEIF @v_pct >= 80 THEN SET NEW.letter_grade='B+', NEW.grade_points=3.30;
        ELSEIF @v_pct >= 75 THEN SET NEW.letter_grade='B',  NEW.grade_points=3.00;
        ELSEIF @v_pct >= 70 THEN SET NEW.letter_grade='B-', NEW.grade_points=2.70;
        ELSEIF @v_pct >= 65 THEN SET NEW.letter_grade='C+', NEW.grade_points=2.30;
        ELSEIF @v_pct >= 60 THEN SET NEW.letter_grade='C',  NEW.grade_points=2.00;
        ELSE                     SET NEW.letter_grade='F',  NEW.grade_points=0.00;
        END IF;
    END IF;
END
""")
conn.commit()
steps.append("✅ Created fixed trg_grade_before_update (BEFORE UPDATE with auto letter grade)")

# Step 8: Add section-limit trigger (if not exists)
cursor.execute("DROP TRIGGER IF EXISTS trg_course_section_limit")
conn.commit()
cursor.execute("""
CREATE TRIGGER trg_course_section_limit
BEFORE INSERT ON courses
FOR EACH ROW
BEGIN
    DECLARE v_count INT DEFAULT 0;
    IF NEW.faculty_id IS NOT NULL THEN
        SELECT COUNT(*) INTO v_count
        FROM courses
        WHERE faculty_id  = NEW.faculty_id
          AND course_code = NEW.course_code
          AND semester    = NEW.semester;
        IF v_count >= 3 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Faculty cannot teach more than 3 sections of the same course per semester';
        END IF;
    END IF;
END
""")
conn.commit()
steps.append("✅ Created trg_course_section_limit trigger (max 3 sections)")

# Step 9: Add multi-section sample courses (if not already there)
cursor.execute("SELECT course_id FROM courses WHERE course_code='CS101' AND section='B'")
if cursor.fetchone():
    print("⚠️  CS101 Section B already exists — skipping sample data")
else:
    cursor.execute("""
        INSERT INTO courses (course_code, course_name, credit_hours, semester, section, faculty_id, max_capacity)
        VALUES ('CS101', 'Introduction to Programming', 3, 'Fall 2026', 'B', 1, 45)
    """)
    cs101b_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO courses (course_code, course_name, credit_hours, semester, section, faculty_id, max_capacity)
        VALUES ('IT220', 'Web Application Development', 3, 'Fall 2026', 'B', 2, 35)
    """)
    it220b_id = cursor.lastrowid

    # Add enrollments
    cursor.execute("""
        INSERT INTO enrollments (student_id, course_id, enrolled_at, status)
        VALUES (3, %s, '2026-08-22 11:30:00', 'active')
    """, (cs101b_id,))
    enroll1_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO enrollments (student_id, course_id, enrolled_at, status)
        VALUES (4, %s, '2026-08-23 12:05:00', 'active')
    """, (it220b_id,))
    enroll2_id = cursor.lastrowid

    # Add grades
    cursor.execute("""
        INSERT INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points)
        VALUES (%s, 67.00, 100.00, 'C+', 2.30)
    """, (enroll1_id,))

    cursor.execute("""
        INSERT INTO grades (enrollment_id, marks_obtained, total_marks, letter_grade, grade_points)
        VALUES (%s, 78.00, 100.00, 'B', 3.00)
    """, (enroll2_id,))

    conn.commit()
    steps.append("✅ Added CS101-B and IT220-B with enrollments & grades")

# Step 10: Recreate views
for view_sql in [
    """CREATE OR REPLACE VIEW v_student_transcript AS
    SELECT s.student_id, CONCAT(s.first_name,' ',s.last_name) AS student_name,
           c.course_code, c.course_name, c.section, c.credit_hours,
           g.marks_obtained, g.total_marks, g.letter_grade, g.grade_points,
           e.status AS enrollment_status, e.enrolled_at
    FROM students s JOIN enrollments e ON s.student_id=e.student_id
    JOIN courses c ON e.course_id=c.course_id LEFT JOIN grades g ON e.enrollment_id=g.enrollment_id""",

    """CREATE OR REPLACE VIEW v_attendance_summary AS
    SELECT e.enrollment_id, e.student_id, e.course_id, c.course_name, c.section,
           COUNT(a.attendance_id) AS total_classes,
           SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) AS classes_attended,
           ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END)/NULLIF(COUNT(a.attendance_id),0)*100,2) AS attendance_percentage
    FROM enrollments e JOIN courses c ON e.course_id=c.course_id
    LEFT JOIN attendance a ON e.enrollment_id=a.enrollment_id
    GROUP BY e.enrollment_id, e.student_id, e.course_id, c.course_name, c.section""",

    """CREATE OR REPLACE VIEW v_course_roster AS
    SELECT c.course_id, c.course_code, c.course_name, c.section,
           CONCAT(f.first_name,' ',f.last_name) AS faculty_name,
           s.student_id, CONCAT(s.first_name,' ',s.last_name) AS student_name, s.email,
           e.enrollment_id, e.enrolled_at, e.status
    FROM courses c JOIN faculty f ON c.faculty_id=f.faculty_id
    JOIN enrollments e ON c.course_id=e.course_id JOIN students s ON e.student_id=s.student_id
    WHERE e.status='active'""",

    """CREATE OR REPLACE VIEW v_admin_enrollment_report AS
    SELECT c.course_id, c.course_code, c.course_name, c.section, c.credit_hours,
           CONCAT(f.first_name,' ',f.last_name) AS faculty_name, c.max_capacity,
           COUNT(e.enrollment_id) AS enrolled_count,
           c.max_capacity-COUNT(e.enrollment_id) AS seats_remaining,
           ROUND(COUNT(e.enrollment_id)/c.max_capacity*100,1) AS fill_percentage
    FROM courses c LEFT JOIN faculty f ON c.faculty_id=f.faculty_id
    LEFT JOIN enrollments e ON c.course_id=e.course_id AND e.status='active'
    GROUP BY c.course_id, c.course_code, c.course_name, c.section, c.credit_hours,
             f.first_name, f.last_name, c.max_capacity"""
]:
    cursor.execute(view_sql)
    conn.commit()
steps.append("✅ Recreated all 4 views with section column")

cursor.close()
conn.close()

print("\n" + "="*50)
print("MIGRATION COMPLETE")
print("="*50)
for s in steps:
    print(s)
print("="*50)
