import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import csv
import os
import logging
from io import StringIO

app = Flask(__name__, 
            static_folder="../frontend/static", 
            template_folder="../frontend/templates")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/submit', methods=['POST'])
def submit_data():
    data = request.json
    table = data['table_select']
    year = data['year_select']
    acs_type = data['acs_type']
    include_metadata = data['include_metadata']
    data_option = data['data_option']
    selected_variables = data['selected_variables'] if data_option == 'select_variables' else None
    geography = data['geography']
    api_key = data['api_key'].strip('"') if data['api_key'] else None

    # Process the data here
    result = fetch_and_save_data(year, table, acs_type, include_metadata, selected_variables, geography, api_key)

    return jsonify(result)

def get_acs_selection(year, acs_type):
    return acs_type

def get_variable_names(year, api_key, variables_needed, acs_selection, tableType):
    api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}{tableType}/variables.json'
    response = requests.get(api_url)
    variables = {}
    if response.status_code == 200:
        data = response.json()
        for var_id, var_info in data['variables'].items():
            if var_id in variables_needed:
                title = (var_info['label'].replace(' ', '_').replace('!!', '_')
                         .replace(',', '').replace('$', '').replace('(', '')
                         .replace(')', '').replace("'", '').replace("-", '').replace("/", '_'))
                variables[var_id] = title
    return variables

@app.route('/process_data', methods=['POST'])
def process_data():
    try:
        data = request.json
        api_url = data['api_url']
        year = data['year_select']
        acs_type = data['acs_type']
        table = data['table_select']
        data_option = data['data_option']
        geography = data['geography']
        api_key = data.get('api_key')

        # Fetch data from the Census API
        response = requests.get(api_url)
        response.raise_for_status()  # This will raise an exception for HTTP errors

        census_data = response.json()

        # Get variable names
        tableType = '/profile' if table.startswith('DP') else ''
        if data_option == 'entire_table':
            variables_needed = [col for col in census_data[0] if col != 'NAME' and not col.startswith('GEO_ID')]
        else:
            variables_needed = data['selected_variables'].split(',') if data['selected_variables'] else []

        variable_names = get_variable_names(year, api_key, variables_needed, acs_type, tableType)

        # Create a pandas DataFrame
        df = pd.DataFrame(census_data[1:], columns=census_data[0])

        # Replace variable codes with names in the DataFrame
        for var_code, var_name in variable_names.items():
            if var_code in df.columns:
                df = df.rename(columns={var_code: f"{var_code}: {var_name}"})

        # Convert DataFrame to HTML table
        table_html = df.to_html(index=False)
        table_html = table_html.replace('class="dataframe"', 'class="data-table"')
        
        available_years = range(2009, 2023)  # Adjust this range as needed
        years = [year]  # For now, just the current year. You can expand this later.

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
    more_variables = request.form.get('moreVariables')
    more_years = request.form.getlist('moreYears')
    
    # Process the new variables and years
    # Update your data accordingly
    # This is a placeholder. You'll need to implement the logic to fetch and process new data.
    
    # For now, we'll just return a success message
    return jsonify({'status': 'success'})

def fetch_and_save_data(year, table, acs_type, include_metadata, selected_variables, geography, api_key):
    output_directory = 'census_data'
    os.makedirs(output_directory, exist_ok=True)

    acs_selection = get_acs_selection(year, acs_type)
    tableType = '/profile' if table.startswith('DP') else '' #TODO

    # Get variables
    if selected_variables:
        variables_needed = selected_variables.split(',')
    else:
        # You might want to get all variables for the table here
        # This is a placeholder and needs to be implemented #TODO 
        variables_needed = []

    variable_names = get_variable_names(year, api_key, variables_needed, acs_selection, tableType)
    
    variables_to_get = ','.join(variables_needed)

    # Construct the API URL
    api_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}{tableType}?get=NAME,GEOID,{variables_to_get}&for={geography}'
    
    # Add the API key to the URL only if it's provided
    if api_key:
        api_url += f'&key={api_key}'

    response = requests.get(api_url)

    if response.status_code == 200:
        try:
            data = response.json()

            if data and len(data) > 1:
                # Add variable names as the second row
                header_row = data[0]
                title_row = ['NAME'] + [variable_names.get(var, var) for var in header_row[1:]] + ['Year']
                data[0].append('Year')
                for row in data[1:]:
                    row.append(year)
                data.insert(1, title_row)

                # Create a CSV file
                csv_filename = f'{output_directory}/{table}_{year}_{acs_selection}.csv'
                with open(csv_filename, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerows(data)

                return {"message": f"Data saved to {csv_filename}"}
            else:
                return {"error": "No data received from the API"}
        except Exception as e:
            return {"error": f"Error processing data: {str(e)}"}
    else:
        return {"error": f"API request failed with status code {response.status_code}"}
    


@app.route('/api/generate_url', methods=['POST'])
def generate_url():
    data = request.json
    table = data['table_select']
    year = data['year_select']
    acs_type = data['acs_type']
    data_option = data['data_option']
    selected_variables = data['selected_variables'] if data_option == 'select_variables' else None
    geography = data['geography']
    api_key = data['api_key'].strip('"') if data['api_key'] else None

    acs_selection = acs_type  # This will be either 'acs1' or 'acs5'

    # Construct the base URL
    base_url = f'https://api.census.gov/data/{year}/acs/{acs_selection}'

    # Handle DP tables (profile tables)
    if table.startswith('DP'):
        if data_option == 'entire_table':
            api_url = f'{base_url}/profile?get=group({table})&for={geography}'
        else:
            api_url = f'{base_url}/profile?get=NAME,{selected_variables}&for={geography}'
    else:
        # Handle other tables (subject tables or detailed tables)
        if data_option == 'entire_table':
            api_url = f'{base_url}?get=group({table})&for={geography}'
        else:
            api_url = f'{base_url}?get=NAME,{selected_variables}&for={geography}'

    # Add the API key to the URL only if it's provided
    if api_key:
        api_url += f'&key={api_key}'

    return jsonify({"api_url": api_url})











if __name__ == '__main__':
    app.run(debug=True)
