from flask import Blueprint, render_template, request, jsonify, session
from backend.database.db_manager import db
from backend.app.auth.decorators import login_required

# Create the Blueprint
search_bp = Blueprint('search', __name__)

# Change @app.route to @search_bp.route for all routes
@search_bp.route('/saved_searches')
@login_required
def saved_searches():
    project_id = request.args.get('project')
    if project_id:
        searches = db.get_project_searches(project_id)
    else:
        searches = db.get_user_searches(session['user_id'])
    
    projects = db.get_user_projects(session['user_id'])
    return render_template('saved_searches.html', searches=searches, projects=projects)

@search_bp.route('/api/rerun_search/<int:search_id>', methods=['POST'])
@login_required
def rerun_search(search_id):
    search = db.get_search(search_id)
    if search and search['user_id'] == session['user_id']:
        return jsonify({'success': True, 'search': search})
    return jsonify({'success': False, 'error': 'Search not found'}), 404

@search_bp.route('/api/save_search/<int:search_id>', methods=['POST'])
@login_required
def save_search(search_id):
    if db.update_search_saved_status(search_id, True):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to save search'}), 400

@search_bp.route('/api/delete_search/<int:search_id>', methods=['DELETE'])
@login_required
def delete_search(search_id):
    if db.delete_search(search_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete search'}), 400
