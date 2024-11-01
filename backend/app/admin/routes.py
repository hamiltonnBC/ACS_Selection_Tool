"""
Admin routes and handlers.
"""
from flask import Blueprint, render_template
from backend.app.auth.decorators import login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Admin dashboard code...
    pass
