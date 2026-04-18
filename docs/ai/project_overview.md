# Project Overview

## Name
Smart Campus Academic Management System

## Purpose
A database-driven full-stack web application that centralizes university academic operations — student enrollment, attendance tracking, grade management, and GPA calculation — into a single relational system.

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Database | MySQL | 8.x |
| Backend | Python + Flask | 3.11 / Flask 3.x |
| DB Driver | mysql-connector-python | latest |
| Auth | Flask sessions + werkzeug password hashing | — |
| Frontend | Jinja2 HTML templates + vanilla CSS/JS | — |
| Dev Tools | MySQL Workbench, VS Code, GitHub Copilot | — |
| OS | Windows 11 | — |

## User Roles

| Role | Username (dev) | Password (dev) | Access |
|---|---|---|---|
| Student | `student` | `1234` | Enroll, view grades, attendance, transcript |
| Faculty | `faculty` | `1234` | Mark attendance, enter grades, view roster |
| Admin | `admin` | `1234` | Manage users, courses, reports |

> Dev login credentials are hardcoded in `blueprints/auth.py`. Remove before any real deployment.

## Core Features

**Student**
- View and enroll in available courses
- View attendance percentage per course (with visual progress bar)
- View grades and letter grade per course
- View calculated CGPA
- View full academic transcript (printable)

**Faculty**
- View assigned courses
- View enrolled student roster per course
- Mark attendance (Present / Absent / Late) per class session
- Enter marks — letter grade auto-calculated via stored procedure

**Admin**
- Add/edit students and faculty (with user account creation)
- Create courses and assign faculty
- View enrollment reports, GPA distribution, faculty load

## Current Status
- Database schema: designed, not yet set up (MySQL not installed)
- Flask backend: code written, running with mock DB connector
- Frontend templates: generated via GitHub Copilot + Google Stitch
- CSS design system: Modern Clean Slate (light + dark mode)
- All fake logins active for frontend-only testing

## Academic Context
This is a DBMS semester project. The implementation must demonstrate:
- Relational schema design (Ch.5)
- SQL DDL/DML (Ch.6)
- Complex queries and Views (Ch.7)
- ER Diagram (Ch.3)
- Normalization to 3NF/BCNF (Ch.14)
- Stored Procedures, Triggers
- Transaction concepts (Ch.20-22)
- NoSQL comparison in project report (Ch.24)