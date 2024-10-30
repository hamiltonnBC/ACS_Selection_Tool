"""
Database helper functions for the ACS Data Application.
Provides an interface for common database operations.
"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import bcrypt
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, database_url: str):
        """Initialize database connection."""
        self.database_url = database_url
        
    def get_connection(self):
        """Create and return a new database connection."""
        return psycopg2.connect(self.database_url)

    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """Create a new user in the database."""
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # First check if username or email already exists
                    cur.execute("""
                        SELECT username, email FROM users 
                        WHERE username = %s OR email = %s
                    """, (username, email))
                    
                    existing = cur.fetchone()
                    if existing:
                        print(f"User already exists: {existing}")  # Debug print
                        return None
                    
                    # If no existing user, create new user
                    cur.execute("""
                        INSERT INTO users (username, email, password_hash)
                        VALUES (%s, %s, %s)
                        RETURNING user_id
                    """, (username, email, password_hash.decode('utf-8')))
                    
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    print(f"Created user with ID: {user_id}")  # Debug print
                    return user_id
                    
        except Exception as e:
            print(f"Error in create_user: {str(e)}")  # Debug print
            conn.rollback() if 'conn' in locals() else None
            return None

    def verify_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verify user credentials and update last login timestamp.
        
        Args:
            username: User's username
            password: Password to verify
            
        Returns:
            User dict if verified, None if not
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT user_id, username, password_hash
                    FROM users
                    WHERE username = %s
                """, (username,))
                user = cur.fetchone()
                
                if user and bcrypt.checkpw(password.encode('utf-8'), 
                                         user['password_hash'].encode('utf-8')):
                    cur.execute("""
                        UPDATE users
                        SET last_login = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """, (user['user_id'],))
                    return dict(user)
                return None

    def create_project(self, user_id: int, project_name: str, 
                      description: Optional[str] = None) -> Optional[int]:
        """Create a new project for a user."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO projects (user_id, project_name, description)
                        VALUES (%s, %s, %s)
                        RETURNING project_id
                    """, (user_id, project_name, description))
                    return cur.fetchone()[0]
                except psycopg2.Error:
                    conn.rollback()
                    return None

    def save_search(self, user_id: int, project_id: int, table_name: str,
                   year: int, acs_type: str, geography: str, 
                   variables: List[str]) -> Optional[int]:
        """Save a search to the database."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO searches 
                        (user_id, project_id, table_name, year, acs_type, 
                         geography, variables)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING search_id
                    """, (user_id, project_id, table_name, year, acs_type,
                          geography, variables))
                    return cur.fetchone()[0]
                except psycopg2.Error:
                    conn.rollback()
                    return None

    def save_ai_interaction(self, project_id: int, user_id: int,
                          query_text: str, response_text: str) -> Optional[int]:
        """Save an AI interaction to the database."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO ai_interactions 
                        (project_id, user_id, query_text, response_text)
                        VALUES (%s, %s, %s, %s)
                        RETURNING interaction_id
                    """, (project_id, user_id, query_text, response_text))
                    return cur.fetchone()[0]
                except psycopg2.Error:
                    conn.rollback()
                    return None

    def get_user_searches(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all searches for a user."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT s.*, p.project_name
                    FROM searches s
                    LEFT JOIN projects p ON s.project_id = p.project_id
                    WHERE s.user_id = %s
                    ORDER BY s.search_timestamp DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    def get_project_searches(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all searches for a project."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT *
                    FROM searches
                    WHERE project_id = %s
                    ORDER BY search_timestamp DESC
                """, (project_id,))
                return [dict(row) for row in cur.fetchall()]
            
    
    def get_search(self, search_id: int) -> Optional[Dict[str, Any]]:
        """Get a single search by ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT s.*, p.project_name
                    FROM searches s
                    LEFT JOIN projects p ON s.project_id = p.project_id
                    WHERE s.search_id = %s
                """, (search_id,))
                result = cur.fetchone()
                return dict(result) if result else None

    def update_search_saved_status(self, search_id: int, is_saved: bool) -> bool:
        """Update the saved status of a search."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        UPDATE searches
                        SET is_saved = %s
                        WHERE search_id = %s
                        RETURNING search_id
                    """, (is_saved, search_id))
                    return cur.fetchone() is not None
                except psycopg2.Error:
                    conn.rollback()
                    return False

    def delete_search(self, search_id: int) -> bool:
        """Delete a search."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        DELETE FROM searches
                        WHERE search_id = %s
                        RETURNING search_id
                    """, (search_id,))
                    return cur.fetchone() is not None
                except psycopg2.Error:
                    conn.rollback()
                    return False

