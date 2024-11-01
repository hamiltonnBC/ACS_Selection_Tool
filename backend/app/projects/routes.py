"""
Project management routes and handlers.
"""
from flask import Blueprint, render_template, request, jsonify, session
from backend.app.auth.decorators import login_required
from backend.database.db_manager import DatabaseManager as db

projects_bp = Blueprint('projects', __name__)

@projects_bp.route('/projects')
@login_required
def projects():
    """Handle project listing and creation."""
    # Get user's projects
    projects = db.get_user_projects(session['user_id'])
    return render_template('projects.html', projects=projects)


@projects_bp.route('/api/projects', methods=['POST'])
@login_required
def create_project():
    """Create a new project."""
    data = request.json
    project_id = db.create_project(
        user_id=session['user_id'],
        project_name=data['project_name'],
        description=data.get('description', '')
    )
    if project_id:
        return jsonify({'success': True, 'project_id': project_id})
    return jsonify({'success': False, 'error': 'Failed to create project'}), 400


@projects_bp.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    """Delete a project."""
    if db.delete_project(project_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete project'}), 400