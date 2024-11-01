"""
Census API interaction functions.
"""
import requests

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