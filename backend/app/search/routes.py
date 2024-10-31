"""
Search routes and handlers.
"""
import requests
from flask import Blueprint, render_template, request, url_for
from werkzeug.utils import redirect

from backend.app.api.census import get_variable_names
from backend.app.auth.decorators import login_required
import pandas as pd

search_bp = Blueprint('search', __name__)

@search_bp.route('/process_data', methods=['GET', 'POST'])
@login_required
def process_data():
    """Process Census data and render visualization."""
    try:
        if request.method == 'GET':
            # Handle GET request with search_id
            search_id = request.args.get('search_id')
            if not search_id:
                return redirect(url_for('index'))

            # Get search data from database
            search = db.get_search(search_id)
            if not search:
                return redirect(url_for('index'))

            # Reconstruct API URL
            if search['table_name'].startswith('DP'):
                api_url = f'https://api.census.gov/data/{search["year"]}/acs/{search["acs_type"]}/profile?get=NAME,{",".join(search["variables"])}&for={search["geography"]}'
            else:
                api_url = f'https://api.census.gov/data/{search["year"]}/acs/{search["acs_type"]}?get=NAME,{",".join(search["variables"])}&for={search["geography"]}'

            # Fetch data using reconstructed URL
            response = requests.get(api_url)
            response.raise_for_status()
            census_data = response.json()

            # Get variable names and process data
            tableType = '/profile' if search['table_name'].startswith('DP') else ''
            variable_names = get_variable_names(
                search['year'],
                None,  # API key not needed for viewing
                search['variables'],
                search['acs_type'],
                tableType
            )

            # Create and format DataFrame
            df = pd.DataFrame(census_data[1:], columns=census_data[0])
            for var_code, var_name in variable_names.items():
                if var_code in df.columns:
                    df = df.rename(columns={var_code: f"{var_code}: {var_name}"})

            # Generate HTML table
            table_html = df.to_html(index=False, classes='display data-table')

            available_years = range(2009, 2023)
            years = [search['year']]

            return render_template('data_display.html',
                                   table_html=table_html,
                                   table_name=search['table_name'],
                                   year=search['year'],
                                   geography=search['geography'],
                                   available_years=available_years,
                                   years=years,
                                   current_year=search['year'],
                                   search=search)
        else:
            # Handle POST request
            data = request.json

            # Extract request parameters
            api_url = data['api_url']
            year = data['year_select']
            acs_type = data['acs_type']
            table = data['table_select']
            data_option = data['data_option']
            geography = data['geography']
            api_key = data.get('api_key')

            # Fetch and process Census data
            response = requests.get(api_url)
            response.raise_for_status()
            census_data = response.json()

            # Get variable names and process data
            tableType = '/profile' if table.startswith('DP') else ''
            variables_needed = ([col for col in census_data[0] if col != 'NAME' and not col.startswith('GEO_ID')]
                                if data_option == 'entire_table'
                                else data['selected_variables'].split(',') if data['selected_variables'] else [])

            variable_names = get_variable_names(year, api_key, variables_needed, acs_type, tableType)

            # Create and format DataFrame
            df = pd.DataFrame(census_data[1:], columns=census_data[0])
            for var_code, var_name in variable_names.items():
                if var_code in df.columns:
                    df = df.rename(columns={var_code: f"{var_code}: {var_name}"})

            # Generate HTML table
            table_html = df.to_html(index=False, classes='display data-table')

            available_years = range(2009, 2023)
            years = [year]

            return render_template('data_display.html',
                                   table_html=table_html,
                                   table_name=table,
                                   year=year,
                                   geography=geography,
                                   available_years=available_years,
                                   years=years,
                                   current_year=year)

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return render_template('data_display.html',
                               error=f"Error processing data: {str(e)}",
                               table_name="Error",
                               year="",
                               geography="",
                               available_years=[],
                               years=[],
                               current_year="")

@search_bp.route('/saved_searches')
@login_required
def saved_searches():
    """Display user's saved searches with optional project filter."""
    project_id = request.args.get('project')
    if project_id:
        searches = db.get_project_searches(project_id)
    else:
        searches = db.get_user_searches(session['user_id'])

    # Get projects for filter dropdown
    projects = db.get_user_projects(session['user_id'])
    return render_template('saved_searches.html', searches=searches, projects=projects)

@search_bp.route('/api/rerun_search/<int:search_id>', methods=['POST'])
@login_required
def rerun_search(search_id):
    """Rerun a saved search."""
    search = db.get_search(search_id)
    if search and search['user_id'] == session['user_id']:
        return jsonify({'success': True, 'search': search})
    return jsonify({'success': False, 'error': 'Search not found'}), 404

@app.route('/api/save_search/<int:search_id>', methods=['POST'])

@search_bp.route('/api/save_search/<int:search_id>', methods=['POST'])
@login_required
def save_search(search_id):
    """Mark a search as saved."""
    if db.update_search_saved_status(search_id, True):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to save search'}), 400

@search_bp.route('/api/delete_search/<int:search_id>', methods=['DELETE'])
@login_required
def delete_search(search_id):
    """Delete a search."""
    if db.delete_search(search_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete search'}), 400