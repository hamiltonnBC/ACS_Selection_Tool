"""
API routes and handlers.
"""
from flask import Blueprint, request, jsonify, session
from backend.app.auth.decorators import login_required
from .census import fetch_and_save_data, get_variable_names
from backend.database.db_manager import DatabaseManager as db
import requests

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/submit', methods=['POST'])
@login_required
def submit_data():
    """Handle data submission requests."""
    try:
        data = request.json
        print("Received data:", data)  # Debug print

        # Save the search to database
        search_id = db.save_search(
            user_id=session['user_id'],
            project_id=data.get('project_id'),
            table_name=data['table_select'],
            year=data['year_select'],
            acs_type=data['acs_type'],
            geography=data['geography'],
            variables=data['selected_variables'].split(',') if data.get('selected_variables') else []
        )

        # Process the data
        result = fetch_and_save_data(
            year=data['year_select'],
            table=data['table_select'],
            acs_type=data['acs_type'],
            include_metadata=data.get('include_metadata', False),
            selected_variables=data.get('selected_variables'),
            geography=data['geography'],
            api_key=data['api_key'].strip('"') if data.get('api_key') else None
        )

        if 'error' in result:
            return jsonify(result), 400

        result['search_id'] = search_id
        return jsonify(result)

    except Exception as e:
        print(f"Error in submit_data: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/generate_url', methods=['POST'])
def generate_url():
    """
    Generate Census API URL based on user parameters.

    Constructs appropriate URL for different table types and data options.
    """
    data = request.json
    table = data['table_select']
    year = data['year_select']
    acs_type = data['acs_type']
    data_option = data['data_option']
    selected_variables = data['selected_variables'] if data_option == 'select_variables' else None
    geography = data['geography']
    api_key = data['api_key'].strip('"') if data['api_key'] else None

    # Construct base URL
    base_url = f'https://api.census.gov/data/{year}/acs/{acs_type}'

    # Generate appropriate URL based on table type and data option
    if table.startswith('DP'):
        api_url = (f'{base_url}/profile?get=group({table})&for={geography}'
                   if data_option == 'entire_table'
                   else f'{base_url}/profile?get=NAME,{selected_variables}&for={geography}')
    else:
        api_url = (f'{base_url}?get=group({table})&for={geography}'
                   if data_option == 'entire_table'
                   else f'{base_url}?get=NAME,{selected_variables}&for={geography}')

    if api_key:
        api_url += f'&key={api_key}'

    return jsonify({"api_url": api_url})

@api_bp.route('/api/debug_url', methods=['POST'])
def debug_url():
    """Debug endpoint to test API URL generation."""
    data = request.json
    try:
        # Test the API URL
        api_url = generate_census_api_url(
            year=data['year_select'],
            table=data['table_select'],
            acs_type=data['acs_type'],
            selected_variables=data.get('selected_variables'),
            geography=data['geography'],
            api_key=data.get('api_key')
        )

        # Try to fetch data
        response = requests.get(api_url)

        return jsonify({
            'api_url': api_url,
            'status_code': response.status_code,
            'response_text': response.text if response.status_code != 200 else 'Success',
            'headers': dict(response.headers)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500