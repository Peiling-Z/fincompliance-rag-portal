-- Database initialization script for FinCompliance RAG Portal
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist
-- Note: This is handled by POSTGRES_DB environment variable

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom functions for text search
CREATE OR REPLACE FUNCTION create_text_search_vector(text)
RETURNS tsvector AS $$
BEGIN
    RETURN to_tsvector('english', $1);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create indexes for better performance
-- These will be created after the application tables are created
-- by the SQLAlchemy models

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE fincompliance TO postgres;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'FinCompliance RAG Portal database initialized successfully';
END $$;
