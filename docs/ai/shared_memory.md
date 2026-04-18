# Shared Memory

Use this file first. It is the compact project index and status log.

## Which file to use
| Need | File |
|---|---|
| Project summary and current status | [project_overview.md](project_overview.md) |
| App structure, DB schema, routes, session keys | [architecture.md](architecture.md) |
| Request/response behavior and form targets | [api_design.md](api_design.md) |
| This file | Project state, conventions, quick reminders |

## Project at a glance
Flask + MySQL university system with three roles: student, faculty, admin. Server-rendered Jinja2 pages, session-based auth, SQL-backed features for enrollment, attendance, grades, and reports.

## Current status
- Done: schema, procedures, views, triggers, Flask app skeleton, templates, CSS, JS.
- In progress: real DB wiring, seed data, fully finished faculty/admin flows, real auth.
- Temporary: mock DB connector and fake login remain for frontend-only testing.

## Key reminders
- Keep logged-in pages extending `base.html`.
- Use CSS variables and the existing modal/theme helpers in `main.js`.
- Replace any fake login or mock DB code before submission.

## DB setup order
1. Run `db/schema.sql`
2. Run `db/stored_procedures.sql`
3. Run `db/views.sql`
4. Run `db/triggers.sql`
5. Run `db/seed_data.sql`
6. Update `.env`
7. Restore real DB connector/auth

## GPA scale
| Marks | Letter | Points |
|---|---|---|
| >= 90 | A | 4.00 |
| >= 85 | A- | 3.70 |
| >= 80 | B+ | 3.30 |
| >= 75 | B | 3.00 |
| >= 70 | B- | 2.70 |
| >= 65 | C+ | 2.30 |
| >= 60 | C | 2.00 |
| < 60 | F | 0.00 |
