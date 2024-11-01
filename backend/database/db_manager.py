"""
Enhanced Database Manager with Security Features
---------------------------------------------
This module provides secure database operations for user authentication and management.
Implements security best practices including:
- Secure password hashing with bcrypt
- Rate limiting and throttling
- Session management
- Audit logging
- Password reset and account activation

References:
- OWASP Authentication Best Practices: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- Password Storage: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- Session Management: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timedelta
import bcrypt
import secrets
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class LoginAttempt:
    """Data class for tracking login attempts"""
    successful: bool
    ip_address: str
    user_agent: str
    failure_reason: Optional[str] = None

class DatabaseManager:
    def __init__(self, database_url: str):
        """
        Initialize database connection and setup logging.

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_connection(self):
        """Create and return a new database connection."""
        return psycopg2.connect(self.database_url)

    def create_user(self, username: str, email: str, password: str) -> Optional[int]:
        """
        Create a new user with security features.

        Security measures:
        - Password hashing with bcrypt
        - Email verification required
        - Duplicate username/email check
        - Activation token generation

        Args:
            username: Desired username
            email: User's email
            password: Plain text password to be hashed

        Returns:
            Optional[int]: User ID if successful, None if failed

        Reference:
        - Secure User Registration: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#implement-proper-password-strength-controls
        """
        try:
            # Generate secure password hash
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

            # Generate activation token
            activation_token = secrets.token_urlsafe(32)

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check for existing user
                    cur.execute("""
                        SELECT username, email FROM users 
                        WHERE username = %s OR email = %s
                    """, (username, email))

                    if cur.fetchone():
                        self.logger.warning(f"Attempted to create duplicate user: {username}")
                        return None

                    # Create new user with activation token
                    cur.execute("""
                        INSERT INTO users (
                            username, email, password_hash, 
                            is_active, activation_token, 
                            activation_token_created_at
                        )
                        VALUES (%s, %s, %s, FALSE, %s, CURRENT_TIMESTAMP)
                        RETURNING user_id
                    """, (username, email, password_hash.decode('utf-8'), activation_token))

                    user_id = cur.fetchone()[0]

                    # Store initial password in history
                    cur.execute("""
                        INSERT INTO password_history (user_id, password_hash)
                        VALUES (%s, %s)
                    """, (user_id, password_hash.decode('utf-8')))

                    return user_id

        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            return None

    def verify_user(self, username: str, password: str, ip_address: str, user_agent: str) -> Optional[Dict[str, Any]]:
        """
        Verify user credentials with security checks.

        Security measures:
        - Brute force protection
        - Login attempt logging
        - Account lockout
        - Last login tracking

        Args:
            username: Username attempting to log in
            password: Password to verify
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Optional[Dict[str, Any]]: User data if verified, None if not

        Reference:
        - Authentication Process: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#authentication-and-error-messages
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    # Check if account is locked
                    cur.execute("""
                        SELECT user_id, username, password_hash, is_active,
                               failed_login_attempts, account_locked_until
                        FROM users
                        WHERE username = %s
                    """, (username,))
                    user = cur.fetchone()

                    if not user:
                        self._log_login_attempt(None, ip_address, user_agent, False, "User not found")
                        return None

                    # Check account lockout
                    if user['account_locked_until'] and user['account_locked_until'] > datetime.now():
                        self._log_login_attempt(
                            user['user_id'], ip_address, user_agent, False,
                            "Account locked"
                        )
                        return None

                    # Verify password
                    if not bcrypt.checkpw(password.encode('utf-8'),
                                          user['password_hash'].encode('utf-8')):
                        # Update failed login attempts
                        cur.execute("""
                            UPDATE users 
                            SET failed_login_attempts = failed_login_attempts + 1,
                                last_failed_login = CURRENT_TIMESTAMP,
                                account_locked_until = CASE 
                                    WHEN failed_login_attempts + 1 >= 5 
                                    THEN CURRENT_TIMESTAMP + interval '15 minutes'
                                    ELSE account_locked_until
                                END
                            WHERE user_id = %s
                        """, (user['user_id'],))

                        self._log_login_attempt(
                            user['user_id'], ip_address, user_agent, False,
                            "Invalid password"
                        )
                        return None

                    # Check if account is activated
                    if not user['is_active']:
                        self._log_login_attempt(
                            user['user_id'], ip_address, user_agent, False,
                            "Account not activated"
                        )
                        return None

                    # Successful login - reset failed attempts and update last login
                    cur.execute("""
                        UPDATE users
                        SET failed_login_attempts = 0,
                            account_locked_until = NULL,
                            last_login = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                    """, (user['user_id'],))

                    self._log_login_attempt(
                        user['user_id'], ip_address, user_agent, True, None
                    )

                    return dict(user)

        except Exception as e:
            self.logger.error(f"Error in verify_user: {str(e)}")
            return None

    def create_session(self, user_id: int, ip_address: str, user_agent: str) -> Optional[str]:
        """
        Create a new session for authenticated user.

        Security measures:
        - Secure random token generation
        - IP and user agent tracking
        - Session expiration

        Reference:
        - Session Management: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
        """
        try:
            session_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO user_sessions (
                            user_id, session_token, ip_address, 
                            user_agent, expires_at
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING session_token
                    """, (user_id, session_token, ip_address, user_agent, expires_at))
                    return cur.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error creating session: {str(e)}")
            return None

    def _log_login_attempt(self, user_id: Optional[int], ip_address: str,
                           user_agent: str, successful: bool, failure_reason: Optional[str]):
        """Log login attempt to database for security auditing."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO login_history (
                            user_id, ip_address, user_agent, 
                            login_successful, failure_reason
                        )
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, ip_address, user_agent, successful, failure_reason))
        except Exception as e:
            self.logger.error(f"Error logging login attempt: {str(e)}")

    def activate_account(self, activation_token: str) -> bool:
        """
        Activate a user account using the activation token.

        Reference:
        - Email Verification: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#implement-proper-password-strength-controls
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users
                        SET is_active = TRUE,
                            activation_token = NULL,
                            activation_token_created_at = NULL
                        WHERE activation_token = %s
                          AND activation_token_created_at > CURRENT_TIMESTAMP - interval '24 hours'
                        RETURNING user_id
                    """, (activation_token,))
                    return cur.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error activating account: {str(e)}")
            return False

    def create_password_reset(self, email: str) -> Optional[str]:
        """
        Create a password reset token.

        Reference:
        - Password Reset: https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html
        """
        try:
            reset_token = secrets.token_urlsafe(32)

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE users
                        SET reset_password_token = %s,
                            reset_password_token_created_at = CURRENT_TIMESTAMP
                        WHERE email = %s
                        RETURNING user_id
                    """, (reset_token, email))

                    if cur.fetchone():
                        return reset_token
                    return None
        except Exception as e:
            self.logger.error(f"Error creating password reset: {str(e)}")
            return None

    def check_rate_limit(self, ip_address: str, endpoint: str) -> bool:
        """
        Check if request should be rate limited.

        Reference:
        - Rate Limiting: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#rate-limiting
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get rate limit rules for endpoint
                    cur.execute("""
                        SELECT max_attempts, time_window
                        FROM throttle_rules
                        WHERE endpoint = %s
                    """, (endpoint,))
                    rule = cur.fetchone()

                    if not rule:
                        return True

                    max_attempts, time_window = rule

                    # Check attempts within time window
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM throttle_log
                        WHERE ip_address = %s
                          AND endpoint = %s
                          AND timestamp > CURRENT_TIMESTAMP - interval '1 second' * %s
                    """, (ip_address, endpoint, time_window))

                    attempt_count = cur.fetchone()[0]

                    # Log attempt
                    is_blocked = attempt_count >= max_attempts
                    cur.execute("""
                        INSERT INTO throttle_log (ip_address, endpoint, is_blocked)
                        VALUES (%s, %s, %s)
                    """, (ip_address, endpoint, is_blocked))

                    return not is_blocked

        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}")
            return False

    # [Original methods remain the same...]
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


    def get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all projects for a user."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT project_id, project_name, description, created_at, updated_at,
                        (SELECT COUNT(*) FROM searches WHERE searches.project_id = projects.project_id) as search_count
                    FROM projects
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                """, (user_id,))
                return [dict(row) for row in cur.fetchall()]

    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all associated searches."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        DELETE FROM projects
                        WHERE project_id = %s
                        RETURNING project_id
                    """, (project_id,))
                    return cur.fetchone() is not None
                except psycopg2.Error:
                    conn.rollback()
                    return False
