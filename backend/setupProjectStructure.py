#!/usr/bin/env python3
"""
Script to create Flask application directory structure.
Creates directories and initial files with basic content.
"""

import os
import shutil

def create_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def create_file(path, content=""):
    """Create file with given content if it doesn't exist."""
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created file: {path}")

def setup_project_structure():
    """Set up the project directory structure and create initial files."""

    # Define the base directory (current directory)
    base_dir = os.getcwd()

    # Define the directories to create
    directories = [
        'app',
        'app/auth',
        'app/admin',
        'app/api',
        'app/projects',
        'app/search',
        'app/utils',
    ]

    # Create directories
    for directory in directories:
        create_directory(os.path.join(base_dir, directory))
        create_file(os.path.join(base_dir, directory, '__init__.py'))

    # Move existing files to their new locations
    if os.path.exists('app.py'):
        shutil.move('app.py', 'app/app.py.old')
        print("Moved app.py to app/app.py.old for reference")

    # Create initial files with placeholder content
    files = {
        'app/__init__.py': '''"""
Flask application factory.
"""
from flask import Flask
from flask_session import Session
from config import Config

db = None

def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder="../../frontend/static",
                template_folder="../../frontend/templates")
    app.config.from_object(config_class)
    
    # Initialize database
    from database.db_manager import DatabaseManager
    global db
    db = DatabaseManager(app.config['DATABASE_URL'])
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.api.routes import api_bp
    from app.projects.routes import projects_bp
    from app.search.routes import search_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(search_bp)
    
    return app
''',

        'app/auth/routes.py': '''"""
Authentication routes and handlers.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.db_manager import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Registration route code...
    pass

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login route code...
    pass

@auth_bp.route('/logout')
def logout():
    # Logout route code...
    pass
''',

        'app/auth/decorators.py': '''"""
Authentication decorators.
"""
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
''',

        'app/auth/utils.py': '''"""
Authentication utility functions.
"""
# Add authentication utility functions here
''',

        'app/admin/routes.py': '''"""
Admin routes and handlers.
"""
from flask import Blueprint, render_template
from app.auth.decorators import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Admin dashboard code...
    pass
''',

        'app/api/routes.py': '''"""
API routes and handlers.
"""
from flask import Blueprint, request, jsonify
from app.auth.decorators import login_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/submit', methods=['POST'])
@login_required
def submit_data():
    # Submit data route code...
    pass
''',

        'app/api/census.py': '''"""
Census API interaction functions.
"""
import requests

def get_acs_selection(year, acs_type):
    # ACS selection code...
    pass

def get_variable_names(year, api_key, variables_needed, acs_selection, tableType):
    # Variable names code...
    pass
''',

        'app/projects/routes.py': '''"""
Project management routes and handlers.
"""
from flask import Blueprint, render_template, request, jsonify, session
from app.auth.decorators import login_required

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects')
@login_required
def projects():
    # Projects route code...
    pass
''',

        'app/search/routes.py': '''"""
Search routes and handlers.
"""
from flask import Blueprint, render_template, request
from app.auth.decorators import login_required

search_bp = Blueprint('search', __name__)

@search_bp.route('/saved_searches')
@login_required
def saved_searches():
    # Saved searches code...
    pass
''',

        'app/utils/helpers.py': '''"""
General utility functions.
"""
# Add utility functions here
''',

        'run.py': '''"""
Application entry point.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
'''
    }

    # Create all files
    for file_path, content in files.items():
        create_file(os.path.join(base_dir, file_path), content)

    print("\nProject structure setup complete!")
    print("\nNext steps:")
    print("1. Move relevant code from app.py.old to the new files")
    print("2. Update imports in each file")
    print("3. Test the application with 'python run.py'")

if __name__ == '__main__':
    setup_project_structure()