-- Initialize PostgreSQL databases for Risk Constellation System

-- Create MLflow database for experiment tracking
CREATE DATABASE mlflow;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE risk_constellation TO riskuser;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO riskuser;

-- Connect to risk_constellation database
\c risk_constellation;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create initial schema (tables will be created by SQLAlchemy)
CREATE SCHEMA IF NOT EXISTS risk_data;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set default schema
ALTER DATABASE risk_constellation SET search_path TO risk_data, public;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.activity_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id VARCHAR(255),
    details JSONB,
    ip_address INET
);

-- Create index on timestamp for faster queries
CREATE INDEX idx_activity_log_timestamp ON audit.activity_log(timestamp DESC);
CREATE INDEX idx_activity_log_user ON audit.activity_log(user_id);

COMMENT ON DATABASE risk_constellation IS 'Main database for AI Risk Constellation System';
COMMENT ON SCHEMA risk_data IS 'Schema for risk assessment data';
COMMENT ON SCHEMA audit IS 'Schema for audit trails and activity logs';