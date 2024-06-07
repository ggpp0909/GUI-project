-- Create tables
CREATE TABLE IF NOT EXISTS work_hours (
    date TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    work_type TEXT
);

-- Create holidays table
CREATE TABLE IF NOT EXISTS holidays (
    date TEXT PRIMARY KEY,
    description TEXT
);

-- Create settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Insert or replace work hours
INSERT OR REPLACE INTO work_hours (date, start_time, end_time, work_type)
VALUES (?, ?, ?, ?);

-- Select all work hours
SELECT * FROM work_hours;

-- Select work hours for a specific date
SELECT start_time, end_time, work_type FROM work_hours WHERE date = ?;

-- Delete work hours
DELETE FROM work_hours WHERE date = ?;

-- Insert or replace holiday
INSERT OR REPLACE INTO holidays (date, description)
VALUES (?, ?);

-- Select all holidays
SELECT * FROM holidays;

-- Delete holiday
DELETE FROM holidays WHERE date = ?;

-- Select holiday description for a specific date
SELECT description FROM holidays WHERE date = ?;

-- Insert or replace remaining leave
INSERT OR REPLACE INTO settings (key, value)
VALUES ('remaining_leave', ?);

-- Select remaining leave
SELECT value FROM settings WHERE key = 'remaining_leave';

-- Drop work_hours table
DROP TABLE IF EXISTS work_hours;

-- Drop holidays table
DROP TABLE IF EXISTS holidays;

-- Drop settings table
DROP TABLE IF EXISTS settings;
