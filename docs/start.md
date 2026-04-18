**Assuming all files are already in the `smart_campus/` folder.**

---

**1. Open the folder in VS Code, then open the terminal (`Ctrl + backtick`)**

**2. Create and activate virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```
You should see `(venv)` appear in the terminal.

**3. Install dependencies**
```bash
pip install flask mysql-connector-python python-dotenv werkzeug
```

**4. Since you have no database yet, patch `db_connector.py`** — replace the entire file content with this mock version temporarily:

```python
def execute_query(query, params=None, fetch=True, many=False):
    return []

def call_procedure(proc_name, args=()):
    return []
```

**5. Set the Flask environment variable**
```bash
set FLASK_APP=app.py
set FLASK_DEBUG=1
```

**6. Run Flask**
```bash
python app.py
```

**7. Open browser at `http://127.0.0.1:5000`**

---

You'll see the login page. Since there's no DB, clicking login won't work — but every template, sidebar, CSS, and layout will render. To preview other pages directly, temporarily add this to the bottom of `app.py` before `app.run`:

```python
@app.route('/preview/<template>')
def preview(template):
    from flask import render_template
    import flask; flask.g.role = 'student'
    return render_template(f'student/{template}.html',
        student={'first_name':'Alex'}, enrolled=[], courses=[],
        records=[], grades=[], cgpa=3.72, transcript=[])
```

Then visit URLs like `http://127.0.0.1:5000/preview/dashboard` to see each page.