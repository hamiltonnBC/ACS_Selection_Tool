/*
 * ACS Data Application Security Schema
 * ----------------------------------
 * This schema implements comprehensive security features following OWASP best practices:
 * https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
 * 
 * Key security features implemented:
 * - Account activation and email verification
 * - Password reset functionality
 * - Session management
 * - Rate limiting and brute force protection
 * - Security audit logging
 * - Admin role management
 */

/* 
 * Users Table
 * -----------
 * Core user information and security settings
 * References:
 * - Password hashing best practices: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
 * - Account lockout: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html#account-lockout
 */
CREATE TABLE users (
                       user_id SERIAL PRIMARY KEY,
                       username VARCHAR(50) UNIQUE NOT NULL,
                       email VARCHAR(255) UNIQUE NOT NULL,
                       password_hash VARCHAR(255) NOT NULL,  -- Stores bcrypt hash (60 chars) with room for future algorithms
                       created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                       last_login TIMESTAMP WITH TIME ZONE,

    -- Account status flags
                       is_active BOOLEAN DEFAULT FALSE,  -- Requires email verification before login
                       is_admin BOOLEAN DEFAULT FALSE,   -- Administrative privileges

    -- Email verification
                       activation_token VARCHAR(100),    -- Secure random token for email verification
                       activation_token_created_at TIMESTAMP WITH TIME ZONE,

    -- Password reset
                       reset_password_token VARCHAR(100),
                       reset_password_token_created_at TIMESTAMP WITH TIME ZONE,

    -- Brute force protection
                       failed_login_attempts INTEGER DEFAULT 0,
                       last_failed_login TIMESTAMP WITH TIME ZONE,
                       account_locked_until TIMESTAMP WITH TIME ZONE
);

/*
 * Session Management
 * -----------------
 * Tracks active user sessions for security
 * References:
 * - Session management: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html
 */
CREATE TABLE user_sessions (
                               session_id SERIAL PRIMARY KEY,
                               user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                               session_token VARCHAR(255) UNIQUE NOT NULL,  -- Secure random session identifier
                               ip_address VARCHAR(45),   -- Supports IPv6 addresses
                               user_agent TEXT,          -- Browser/client identification
                               created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                               expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                               is_active BOOLEAN DEFAULT TRUE
);

/*
 * Security Audit Logging
 * ---------------------
 * Tracks all login attempts for security monitoring
 * References:
 * - Logging: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
 */
CREATE TABLE login_history (
                               login_id SERIAL PRIMARY KEY,
                               user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                               login_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                               ip_address VARCHAR(45),
                               user_agent TEXT,
                               login_successful BOOLEAN,
                               failure_reason TEXT
);

/*
 * Rate Limiting
 * ------------
 * Prevents abuse of authentication endpoints
 * References:
 * - Rate limiting: https://cheatsheetseries.owasp.org/cheatsheets/DOS_Prevention_Cheat_Sheet.html
 */
CREATE TABLE throttle_rules (
                                rule_id SERIAL PRIMARY KEY,
                                endpoint VARCHAR(100) NOT NULL,      -- API endpoint to protect
                                max_attempts INTEGER NOT NULL,       -- Maximum attempts allowed
                                time_window INTEGER NOT NULL,        -- Time window in seconds
                                lockout_duration INTEGER NOT NULL    -- Lockout duration in seconds
);

CREATE TABLE throttle_log (
                              log_id SERIAL PRIMARY KEY,
                              ip_address VARCHAR(45) NOT NULL,
                              endpoint VARCHAR(100) NOT NULL,
                              timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                              is_blocked BOOLEAN DEFAULT FALSE
);

/*
 * Projects Table
 * -------------
 * Stores ACS data project information
 */
CREATE TABLE projects (
                          project_id SERIAL PRIMARY KEY,
                          user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                          project_name VARCHAR(100) NOT NULL,
                          description TEXT,
                          created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                          updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

/*
 * Searches Table
 * -------------
 * Tracks ACS data search history
 */
CREATE TABLE searches (
                          search_id SERIAL PRIMARY KEY,
                          user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                          project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
                          table_name VARCHAR(50) NOT NULL,
                          year INTEGER NOT NULL,
                          acs_type VARCHAR(10) NOT NULL,
                          geography VARCHAR(50) NOT NULL,
                          variables TEXT[],
                          search_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                          is_saved BOOLEAN DEFAULT false
);

/*
 * Saved Variables Table
 * --------------------
 * Stores frequently used ACS variables
 */
CREATE TABLE saved_variables (
                                 variable_id SERIAL PRIMARY KEY,
                                 user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                                 variable_code VARCHAR(20) NOT NULL,
                                 variable_name TEXT NOT NULL,
                                 description TEXT,
                                 created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

/*
 * AI Interactions Table
 * --------------------
 * Stores AI-assisted data analysis history
 */
CREATE TABLE ai_interactions (
                                 interaction_id SERIAL PRIMARY KEY,
                                 project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE,
                                 user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                                 query_text TEXT NOT NULL,
                                 response_text TEXT,
                                 interaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                                 is_saved BOOLEAN DEFAULT false
);

/*
 * Performance Optimization
 * ----------------------
 * Indexes for frequently accessed columns
 * References:
 * - PostgreSQL indexing: https://www.postgresql.org/docs/current/indexes.html
 */
-- User authentication indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_activation_token ON users(activation_token);
CREATE INDEX idx_users_reset_password_token ON users(reset_password_token);

-- Session management indexes
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);

-- Security logging indexes
CREATE INDEX idx_login_history_user_id ON login_history(user_id);
CREATE INDEX idx_login_history_timestamp ON login_history(login_timestamp);

-- Rate limiting indexes
CREATE INDEX idx_throttle_log_ip_endpoint ON throttle_log(ip_address, endpoint);
CREATE INDEX idx_throttle_log_timestamp ON throttle_log(timestamp);

-- Application indexes
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_searches_user_id ON searches(user_id);
CREATE INDEX idx_searches_project_id ON searches(project_id);
CREATE INDEX idx_ai_interactions_project_id ON ai_interactions(project_id);
CREATE INDEX idx_ai_interactions_user_id ON ai_interactions(user_id);

/*
 * Automatic Timestamp Updates
 * -------------------------
 * Maintains data integrity for timestamp fields
 */
CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

/*
 * Default Rate Limiting Rules
 * -------------------------
 * Establishes baseline protection for critical endpoints
 */
INSERT INTO throttle_rules (endpoint, max_attempts, time_window, lockout_duration) VALUES
('login', 5, 300, 900),            -- 5 attempts per 5 minutes, 15 minute lockout
('password_reset', 3, 3600, 7200), -- 3 attempts per hour, 2 hour lockout
('register', 3, 3600, 7200),       -- 3 attempts per hour, 2 hour lockout
('activation', 3, 86400, 86400);   -- 3 attempts per day, 1 day lockout

/*
 * Security Implementation Notes
 * ---------------------------
 * 1. Password hashing must use bcrypt with work factor ≥ 12
 * 2. Session tokens must use cryptographically secure random generation
 * 3. All user input must be validated and sanitized
 * 4. Use prepared statements for all queries
 * 5. Implement proper error handling without exposing sensitive information
 * 6. Monitor login_history and throttle_log for security events
 * 7. Set secure password requirements (minimum length, complexity)
 * 8. Implement CSRF protection in the application layer
 * 9. Use HTTPS for all connections
 * 10. Regular security audits of login patterns
 */