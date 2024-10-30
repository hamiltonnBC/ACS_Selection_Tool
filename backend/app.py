"""
American Community Survey (ACS) Data Processing Application

This Flask application provides an interface for accessing and processing ACS data 
from the Census Bureau API. It allows users to select variables, years, and geographic
levels for data retrieval and visualization.

Main features:
- Variable selection and data retrieval from Census API
- Data processing and formatting
- CSV export functionality
- Web interface for data visualization
"""

from datetime import timedelta
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import pandas as pd
import csv
import os
import logging
from dotenv import load_dotenv
from io import StringIO
from database.db_manager import DatabaseManager
from functools import wraps

#from db_helper import DatabaseManager


# Load environment variables from .env file
load_dotenv()

# Get configuration from environment variables
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://acs_user:Nick_ACS_DB_Password@localhost:5432/acs_db')
SECRET_KEY = os.getenv('SECRET_KEY')

# Create a database instance
#db = None

# Initialize Flask application
app = Flask(__name__, 
            static_folder="../frontend/static", 
            template_folder="../frontend/templates")

# Configure app
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY set in environment variables")
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize database manager
db = DatabaseManager('postgresql://acs_user:Nick_ACS_DB_Password@localhost:5432/acs_db')

# def create_app():
#     """Initialize and configure the Flask application."""
#     app = Flask(__name__,
#                 static_folder="../frontend/static",
#                 template_folder="../frontend/templates")
    
#     # Configure app
#     app.config['SECRET_KEY'] = SECRET_KEY
#     app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Optional: sets how long sessions last
    
#     # Initialize database
#     global db
#     app.db = DatabaseManager(DATABASE_URL)
    
#     # Configure logging
#     logging.basicConfig(level=logging.INFO)
    
#     return app

def login_required(f):
    """Decorator to require login for specific routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_acs_selection(year, acs_type):
    """
    Determine the ACS selection type based on year and ACS type.
    
    Args:
        year (str): The year for data selection
        acs_type (str): Type of ACS survey (1-year or 5-year)
    
    Returns:
        str: ACS selection type
    """
    return acs_type
    

def get_variable_names(year, api_key, variables_needed, acs_selection, tableType):
    """
    Fetch variable names and metadata from the Census API.
    
    Args:
        year (str): Year of data
        api_key (str): Census API key
        variables_needed (list): List of variable codes
        acs_selection (str): ACS selection type
        tableType (str): Type of table ('/profile' or '')
    
    Returns:
        dict: Dictionary mapping variable codes to their descriptions
    """
    api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}{tableType}/variables.json'
    response = requests.get(api_url)
    variables = {}
    
    if response.status_code == 200:
        data = response.json()
        for var_id, var_info in data['variables'].items():
            if var_id in variables_needed:
                # Clean up variable names by removing special characters
                title = (var_info['label'].replace(' ', '_').replace('!!', '_')
                         .replace(',', '').replace('$', '').replace('(', '')
                         .replace(')', '').replace("'", '').replace("-", '').replace("/", '_'))
                variables[var_id] = title
    return variables

def fetch_and_save_data(year, table, acs_type, include_metadata, selected_variables, geography, api_key):
    """Fetch data from Census API and save to CSV file."""
    try:
        output_directory = 'census_data'
        os.makedirs(output_directory, exist_ok=True)

        acs_selection = get_acs_selection(year, acs_type)
        tableType = '/profile' if table.startswith('DP') else ''

        # Process variables
        if selected_variables:
            variables_needed = selected_variables.split(',')
        else:
            variables_needed = []

        variable_names = get_variable_names(year, api_key, variables_needed, acs_selection, tableType)
        variables_to_get = ','.join(variables_needed)

        # Construct API URL
        if table.startswith('DP'):
            if not selected_variables:
                api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}/profile?get=group({table})&for={geography}'
            else:
                api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}/profile?get=NAME,{variables_to_get}&for={geography}'
        else:
            if not selected_variables:
                api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}?get=group({table})&for={geography}'
            else:
                api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}?get=NAME,{variables_to_get}&for={geography}'

        if api_key:
            api_url += f'&key={api_key}'

        print(f"Requesting URL: {api_url}")  # Debug print

        # Fetch and process data
        response = requests.get(api_url)
        if response.status_code != 200:
            error_message = f"API request failed with status code {response.status_code}. Response: {response.text}"
            print(error_message)  # Debug print
            return {"error": error_message}

        try:
            data = response.json()
        except Exception as e:
            return {"error": f"Failed to parse API response: {str(e)}"}

        if not data or len(data) <= 1:
            return {"error": "No data received from the API"}

        # Format data with headers and save to CSV
        header_row = data[0]
        title_row = ['NAME'] + [variable_names.get(var, var) for var in header_row[1:]] + ['Year']
        data[0].append('Year')
        for row in data[1:]:
            row.append(year)
        data.insert(1, title_row)

        csv_filename = f'{output_directory}/{table}_{year}_{acs_selection}.csv'
        with open(csv_filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(data)

        return {"message": f"Data saved to {csv_filename}"}

    except Exception as e:
        print(f"Error in fetch_and_save_data: {str(e)}")  # Debug print
        return {"error": f"Error processing data: {str(e)}"}

# Flask route handlers

@app.route('/register', methods=['GET', 'POST'])
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

@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('index'))


@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html')

 
@app.route('/api/submit', methods=['POST'])
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

@app.route('/process_data', methods=['GET', 'POST'])
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
            # Your existing POST request handling
            data = request.json
            # ... rest of your existing POST handling code ...

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500
    try:
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
        table_html = df.to_html(index=False).replace('class="dataframe"', 'class="data-table"')
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/update_data', methods=['POST'])
def update_data():
    """Handle requests to update data with additional variables or years."""
    more_variables = request.form.get('moreVariables')
    more_years = request.form.getlist('moreYears')
    return jsonify({'status': 'success'})

@app.route('/api/generate_url', methods=['POST'])
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


# @app.route('/api/save_search', methods=['POST'])
# def save_search():
#     data = request.json
#     search_id = db.save_search(
#         user_id=data['user_id'],
#         project_id=data['project_id'],
#         table_name=data['table_select'],
#         year=data['year_select'],
#         acs_type=data['acs_type'],
#         geography=data['geography'],
#         variables=data['selected_variables'].split(',')
#     )
#     return jsonify({"search_id": search_id})

@app.route('/saved_searches')
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

@app.route('/api/rerun_search/<int:search_id>', methods=['POST'])
@login_required
def rerun_search(search_id):
    """Rerun a saved search."""
    search = db.get_search(search_id)
    if search and search['user_id'] == session['user_id']:
        return jsonify({'success': True, 'search': search})
    return jsonify({'success': False, 'error': 'Search not found'}), 404

@app.route('/api/save_search/<int:search_id>', methods=['POST'])
@login_required
def save_search(search_id):
    """Mark a search as saved."""
    if db.update_search_saved_status(search_id, True):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to save search'}), 400

@app.route('/api/delete_search/<int:search_id>', methods=['DELETE'])
@login_required
def delete_search(search_id):
    """Delete a search."""
    if db.delete_search(search_id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to delete search'}), 400

@app.route('/api/debug_url', methods=['POST'])
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
    

def main():
    """
    Main entry point for the application.
    
    Initializes the Flask application and starts the server.
    """
    #app = create_app()
    app.run(debug=True)

if __name__ == '__main__':
    main()
