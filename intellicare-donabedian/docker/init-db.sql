-- ========================================
-- IntelliCare Donabedian - Database Initialization
-- ========================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;

-- Grant permissions to the user
GRANT ALL PRIVILEGES ON SCHEMA intellicare_donabedian TO intellicare;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA intellicare_donabedian TO intellicare;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA intellicare_donabedian TO intellicare;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA intellicare_donabedian GRANT ALL ON TABLES TO intellicare;
ALTER DEFAULT PRIVILEGES IN SCHEMA intellicare_donabedian GRANT ALL ON SEQUENCES TO intellicare;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Schema intellicare_donabedian created successfully';
END $$;

