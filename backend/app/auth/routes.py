"""
Authentication routes and handlers.
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from backend.database.db_manager import DatabaseManager as db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        try:
            data = request.json
            print("Received registration data:", data)  # Debug print

            if not all([data.get('username'), data.get('email'), data.get('password')]):
                return jsonify({'success': False, 'error': 'Missing required fields'})

            user_id = db.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password']
            )
            print("Returned user_id:", user_id)  # Debug print

            if user_id:
                return jsonify({'success': True, 'user_id': user_id})
            return jsonify({'success': False, 'error': 'Registration failed'})
        except Exception as e:
            print(f"Registration error: {str(e)}")  # Debug print
            return jsonify({'success': False, 'error': str(e)})
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        data = request.json
        user = db.verify_user(
            username=data['username'],
            password=data['password']
        )
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Invalid credentials'})
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('index'))
