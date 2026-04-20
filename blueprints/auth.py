from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db_connector import execute_query
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET','POST'])
@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        rows = execute_query(
            "SELECT * FROM users WHERE username=%s AND is_active=1",
            (username,)
        )
        # check_password_hash(rows[0]['password'], password)
        if rows:
            user = rows[0]
            session['user_id']  = user['user_id']
            session['username'] = user['username']
            session['role']     = user['role']

            # Fetch entity-specific ID
            if user['role'] == 'student':
                r = execute_query("SELECT student_id FROM students WHERE user_id=%s",(user['user_id'],))
                session['entity_id'] = r[0]['student_id'] if r else None
                return redirect(url_for('student.dashboard'))
            elif user['role'] == 'faculty':
                r = execute_query("SELECT faculty_id FROM faculty WHERE user_id=%s",(user['user_id'],))
                session['entity_id'] = r[0]['faculty_id'] if r else None
                return redirect(url_for('faculty.dashboard'))
            else:
                return redirect(url_for('admin.dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template('auth/login.html')

# @auth_bp.route('/', methods=['GET','POST'])
# @auth_bp.route('/login', methods=['GET','POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         # Fake users for frontend testing — remove when DB is ready
#         fake_users = {
#             'student': {'user_id': 1, 'username': 'student', 'role': 'student', 'entity_id': 1},
#             'faculty': {'user_id': 2, 'username': 'faculty', 'role': 'faculty', 'entity_id': 1},
#             'admin':   {'user_id': 3, 'username': 'admin',   'role': 'admin',   'entity_id': 1},
#         }

#         if username in fake_users and password == '1234':
#             user = fake_users[username]
#             session['user_id']   = user['user_id']
#             session['username']  = user['username']
#             session['role']      = user['role']
#             session['entity_id'] = user['entity_id']

#             if user['role'] == 'student':
#                 return redirect(url_for('student.dashboard'))
#             elif user['role'] == 'faculty':
#                 return redirect(url_for('faculty.dashboard'))
#             else:
#                 return redirect(url_for('admin.dashboard'))

#         flash("Invalid credentials.", "danger")
#     return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))