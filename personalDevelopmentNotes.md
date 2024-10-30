Creating the database

psql -U postgres
CREATE DATABASE acs_db;
\c acs_db
\i backend/schema/init_db.sql
