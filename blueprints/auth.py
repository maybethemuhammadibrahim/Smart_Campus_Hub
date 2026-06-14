check_password = False

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db_connector import execute_query
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        selected_role = request.form.get('role', '').strip().lower()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template('auth/login.html')

        if selected_role not in ('student', 'faculty', 'admin'):
            flash("Please select a valid login portal.", "danger")
            return render_template('auth/login.html')

        rows = execute_query(
            "SELECT * FROM users WHERE username=%s AND is_active=1",
            (username,)
        )

        if not rows:
            flash("Invalid credentials.", "danger")
            return render_template('auth/login.html')

        user = rows[0]

        # --- Password validation ---
        stored_pw = user['password']
        password_ok = False
        try:
            password_ok = check_password_hash(stored_pw, password)
        except Exception:
            pass
        if not password_ok:
            password_ok = (stored_pw == password)

        if not password_ok:
            flash("Invalid credentials.", "danger")
            return render_template('auth/login.html')

        # --- Role-tab validation ---
        if user['role'] != selected_role:
            flash("Please use the correct login portal for your role.", "warning")
            return render_template('auth/login.html')

        # --- Auth success: set session ---
        session['user_id']  = user['user_id']
        session['username'] = user['username']
        session['role']     = user['role']

        if user['role'] == 'student':
            r = execute_query("SELECT student_id FROM students WHERE user_id=%s", (user['user_id'],))
            session['entity_id'] = r[0]['student_id'] if r else None
            return redirect(url_for('student.dashboard'))

        elif user['role'] == 'faculty':
            r = execute_query("SELECT faculty_id FROM faculty WHERE user_id=%s", (user['user_id'],))
            session['entity_id'] = r[0]['faculty_id'] if r else None
            return redirect(url_for('faculty.dashboard'))

        else:
            return redirect(url_for('admin.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))