# ACS Data Simplification Application

## Purpose

The American Community Survey (ACS) Data Simplification Application is designed to streamline and enhance the process of working with ACS data. This web-based tool addresses several challenges researchers and data analysts face when dealing with ACS datasets, particularly the complexities associated with variable codes and titles that change over time.

## Key Features

### 1. Intuitive Variable Selection

- Users can easily select the years for which they need data.
- The application provides a user-friendly interface for choosing variables of interest.

### 2. Automatic Code Adjustment

- The core functionality of the application is its ability to automatically adjust variable codes across different years.
- When a user selects a variable and a range of years, the system checks for any changes in the variable code or title during those years.
- If changes are detected, the application automatically uses the correct code for each specific year, ensuring data consistency and accuracy.

### 3. Visual Data Representation

- Users can select variables for the X and Y axes.
- The application offers various visualization options, including:
  - Bar plots
  - Scatter plots
  - Line graphs
  - Heat maps
  - Box plots
  - Pie charts (for categorical data)
- Interactive features allow users to zoom, pan, and hover over data points for more information.

### 4. Data Comparison Tools

- Side-by-side comparison of variables across different years or geographic areas.
- Calculation of percent changes or differences between selected years.

### 5. Export Functionality

- Users can export their selected data in various formats (CSV, Excel, JSON).
- Option to export generated visualizations as image files (PNG, SVG) or interactive HTML.

### 6. Metadata Information

- Detailed descriptions of each variable are provided, including any changes in definition over time.
- Links to official ACS documentation for each variable.

### 7. Geographic Customization

- Users can select specific geographic levels (national, state, county, census tract, etc.).
- Option to compare data across different geographic areas.

### 8. API Integration

- Direct integration with the Census Bureau's API, eliminating the need for users to manage API keys or construct complex queries.
