# API Design

Use this file for request flow, form targets, and what each route returns.

## Pattern
- GET renders a template.
- POST changes data and redirects back.
- No JSON API.

## Auth
| Method | Route | Result |
|---|---|---|
| GET/POST | `/login` | validate creds and set session |
| GET | `/logout` | clear session and redirect |

## Student
| Method | Route | Returns |
|---|---|---|
| GET | `/student/dashboard` | student info + active enrollments |
| GET | `/student/courses` | available courses |
| POST | `/student/enroll/<course_id>` | calls `RegisterStudentInCourse` |
| GET | `/student/attendance` | `v_attendance_summary` |
| GET | `/student/grades` | transcript rows + CGPA |
| GET | `/student/transcript` | printable transcript |

## Faculty
| Method | Route | Returns |
|---|---|---|
| GET | `/faculty/dashboard` | faculty profile + assigned courses |
| GET | `/faculty/my-courses` | assigned courses |
| GET | `/faculty/roster` or `/faculty/roster/<course_id>` | course roster |
| GET | `/faculty/attendance` or `/faculty/attendance/<course_id>` | selected course + students |
| POST | `/faculty/attendance/submit` | inserts attendance rows |
| GET | `/faculty/grades` or `/faculty/grades/<course_id>` | students + current grades |
| POST | `/faculty/grades/save` | updates marks/grades |

## Admin
| Method | Route | Returns |
|---|---|---|
| GET | `/admin/dashboard` | counts + recent activity |
| GET | `/admin/students` | students joined with users |
| POST | `/admin/students/add` | creates user + student |
| GET | `/admin/faculty` | faculty joined with users |
| POST | `/admin/faculty/add` | creates user + faculty |
| GET | `/admin/courses` | courses + enrollment stats |
| POST | `/admin/courses/create` | creates course |
| GET | `/admin/reports` | enrollment, GPA, faculty load |

## Form targets
| Form | POST to |
|---|---|
| Login | `/login` |
| Mark attendance | `/faculty/submit_attendance` |
| Enter grades | `/faculty/save_grades` |
| Add student | `/admin/students/add` |
| Add faculty | `/admin/faculty/add` |
| Create course | `/admin/courses/create` |
