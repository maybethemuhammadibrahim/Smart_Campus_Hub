from flask import Flask
from config import Config
from blueprints.auth    import auth_bp
from blueprints.student import student_bp
from blueprints.faculty import faculty_bp
from blueprints.admin   import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(admin_bp,   url_prefix='/admin')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)