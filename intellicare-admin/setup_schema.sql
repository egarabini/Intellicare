CREATE SCHEMA IF NOT EXISTS platform;
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin_module_role') THEN
        CREATE ROLE admin_module_role;
    END IF;
END $$;
GRANT ALL ON SCHEMA platform TO admin_module_role;
