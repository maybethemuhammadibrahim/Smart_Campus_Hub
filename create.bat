@echo off

type nul > app.py
type nul > config.py
type nul > .env
type nul > requirements.txt
type nul > db_connector.py
type nul > decorators.py

mkdir db 2>nul
cd db
type nul > schema.sql
type nul > stored_procedures.sql
type nul > views.sql
type nul > triggers.sql
type nul > seed_data.sql
mkdir queries 2>nul
cd queries
type nul > student_queries.sql
type nul > faculty_queries.sql
type nul > admin_queries.sql
cd ..\..
mkdir blueprints 2>nul
cd blueprints
type nul > __init__.py
type nul > auth.py
type nul > student.py
type nul > faculty.py
type nul > admin.py
cd ..
mkdir templates 2>nul
cd templates
type nul > base.html
mkdir auth 2>nul
cd auth
type nul > login.html
cd ..
mkdir student 2>nul
cd student
type nul > dashboard.html
type nul > courses.html
type nul > my_courses.html
type nul > attendance.html
type nul > grades.html
type nul > transcript.html
cd ..
mkdir faculty 2>nul
cd faculty
type nul > dashboard.html
type nul > my_courses.html
type nul > roster.html
type nul > mark_attendance.html
type nul > enter_grades.html
cd ..
mkdir admin 2>nul
cd admin
type nul > dashboard.html
type nul > students.html
type nul > faculty.html
type nul > courses.html
type nul > reports.html
type nul > assign_faculty.html
cd ..\..
mkdir static 2>nul
cd static
mkdir css 2>nul
cd css
type nul > style.css
cd ..
mkdir js 2>nul
cd js
type nul > main.js
cd ..\..

echo Folder structure created successfully in smart_campus directory.c