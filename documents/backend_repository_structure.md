# Backend Repository Structure Documentation

## Overview
This document explains the structure and organization of the backend repository for the ACS Data Application with integrated User Authentication System. The application follows a modular design pattern using Flask blueprints and package-based organization.

## Directory Structure

### Root Directory Components

#### `run.py`
- Main entry point for the application
- Initializes and runs the Flask application
- Loads configuration and starts the development server

#### `config.py`
- Contains application configuration settings
- Manages environment variables
- Defines configuration classes for different environments (development, production)

#### `requirements.txt`
- Lists all Python dependencies required by the application
- Used for environment setup and deployment
- Ensures consistent dependency versions across installations

### Application Modules

#### `app/` Directory
The main application package containing all application logic, organized into feature-specific subpackages.

##### `app/__init__.py`
- Application factory function
- Blueprint registration
- Database initialization
- Extension initialization

##### `app/auth/` - Authentication Package
Handles user authentication and authorization.
- `__init__.py`: Package initialization
- `routes.py`: Authentication endpoints (login, register, logout)
- `decorators.py`: Security decorators (login_required, etc.)
- `utils.py`: Authentication helper functions

##### `app/admin/` - Administration Package
Manages administrative functions.
- `__init__.py`: Package initialization
- `routes.py`: Admin dashboard and management endpoints

##### `app/api/` - API Package
Handles external API interactions and data processing.
- `__init__.py`: Package initialization
- `census.py`: Census API interaction functions
- `routes.py`: API endpoints for data retrieval and processing

##### `app/projects/` - Projects Package
Manages user projects and related functionality.
- `__init__.py`: Package initialization
- `routes.py`: Project management endpoints

##### `app/search/` - Search Package
Handles search functionality and history.
- `__init__.py`: Package initialization
- `routes.py`: Search-related endpoints

##### `app/utils/` - Utilities Package
Contains shared utility functions.
- `__init__.py`: Package initialization
- `helpers.py`: General helper functions

### Database Components

#### `database/` Directory
Contains database-related code and configurations.

##### `db_manager.py`
- Database connection management
- SQL query execution
- Data access layer implementation

##### `schema/init_db.sql`
- SQL schema definitions
- Database initialization scripts
- Table creation and indexing

### Data Storage

#### `census_data/` Directory
- Stores downloaded Census data files
- Contains CSV files with ACS data
- Naming format: `{table}_{year}_{acs_type}.csv`

### Cache and Compilation Files

#### `__pycache__/` Directories
- Python bytecode cache
- Automatically generated
- Improves application load time
- Should not be version controlled

## Key Features Organization

### Authentication System
- Located in `app/auth/`
- Implements user registration, login, and session management
- Provides security decorators for route protection
- Manages user authentication state

### Data Processing
- Centered in `app/api/`
- Handles Census API interactions
- Processes and formats data
- Manages data storage and retrieval

### Project Management
- Implemented in `app/projects/`
- Handles user project organization
- Manages project-related data operations
- Provides project visualization tools

### Search Functionality
- Contained in `app/search/`
- Implements search history tracking
- Provides search result management
- Handles data filtering and sorting

### Administrative Features
- Located in `app/admin/`
- Provides system administration tools
- Manages user accounts and permissions
- Monitors system usage and performance

## Best Practices

### Modularity
- Each package is self-contained
- Clear separation of concerns
- Minimized dependencies between modules
- Easy to maintain and extend

### Security
- Authentication checks implemented consistently
- Sensitive data properly protected
- Security best practices enforced
- Rate limiting and access control implemented

### Database Access
- Centralized database management
- Consistent error handling
- Connection pooling
- Prepared statements for SQL injection prevention

### Configuration
- Environment-based configuration
- Secure credential management
- Flexible deployment options
- Easy environment switching

## Development Workflow

### Local Development
1. Run `run.py` for development server
2. Use environment variables for configuration
3. Access application at localhost:5000

### Database Updates
1. Modify schema in `init_db.sql`
2. Update `db_manager.py` as needed
3. Apply changes to database

### Adding New Features
1. Create new package if needed
2. Implement routes and logic
3. Register blueprints in `app/__init__.py`
4. Update documentation