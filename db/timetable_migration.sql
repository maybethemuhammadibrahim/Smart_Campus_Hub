
CREATE TABLE IF NOT EXISTS timetable_slots (
    slot_id      INT AUTO_INCREMENT PRIMARY KEY,
    section_id   INT NOT NULL,
    day_of_week  ENUM('Mon','Tue','Wed','Thu','Fri') NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    room         VARCHAR(50) DEFAULT '',
    CONSTRAINT fk_tt_section FOREIGN KEY (section_id)
        REFERENCES course_sections(section_id) ON DELETE CASCADE,
    CONSTRAINT uq_tt_slot UNIQUE (section_id, day_of_week, start_time)
);

CREATE INDEX IF NOT EXISTS idx_tt_section ON timetable_slots(section_id);
CREATE INDEX IF NOT EXISTS idx_tt_day     ON timetable_slots(day_of_week);
