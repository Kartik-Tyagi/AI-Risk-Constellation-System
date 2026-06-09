-- Migration: 001_initial_schema
-- Description: Initial database schema setup
-- Date: 2024-06-09

-- This migration is applied by the main postgres_schema.sql file
-- Future migrations should be numbered sequentially (002, 003, etc.)

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Record this migration
INSERT INTO schema_migrations (migration_name, description)
VALUES ('001_initial_schema', 'Initial database schema setup')
ON CONFLICT (migration_name) DO NOTHING;