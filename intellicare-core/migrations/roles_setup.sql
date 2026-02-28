#!/bin/bash
# PostgreSQL Role Setup Script for IntelliCare
#
# This script creates PostgreSQL roles and sets up initial credentials.
# Should be run as a PostgreSQL superuser (usually 'postgres').
#
# Usage:
#   psql -U postgres -d intellicare_db -f roles_setup.sql
#
# Or interactively:
#   sudo -u postgres psql
#   \i roles_setup.sql

-- ============================================================================
-- CREATE ROLES WITH PASSWORDS
-- ============================================================================

-- Operational user (for transactional writes)
CREATE ROLE operacional_user WITH LOGIN PASSWORD 'CHANGE_ME_operacional_secure_password_here';
ALTER ROLE operacional_user SET statement_timeout = '30s';  -- Prevent long-running queries
ALTER ROLE operacional_user VALID UNTIL '2027-12-31';  -- Optional expiration

-- Analytics user (for read-only access)
CREATE ROLE analytics_user WITH LOGIN PASSWORD 'CHANGE_ME_analytics_secure_password_here';
ALTER ROLE analytics_user SET statement_timeout = '60s';  -- Longer timeout for analytics queries
ALTER ROLE analytics_user SET default_transaction_isolation = 'read only';
ALTER ROLE analytics_user VALID UNTIL '2027-12-31';

-- Admin user (for migrations and maintenance)
CREATE ROLE intellicare_admin WITH LOGIN PASSWORD 'CHANGE_ME_admin_secure_password_here';
ALTER ROLE intellicare_admin SET statement_timeout = '120s';
ALTER ROLE intellicare_admin VALID UNTIL '2027-12-31';

-- Optional: Create app service account (for Python/FastAPI)
CREATE ROLE intellicare_app_service WITH LOGIN PASSWORD 'CHANGE_ME_app_secure_password_here';
GRANT operacional_user TO intellicare_app_service;
GRANT analytics_user TO intellicare_app_service;

-- ============================================================================
-- GRANT BASIC SCHEMA PERMISSIONS
-- ============================================================================

-- Core schemas
GRANT USAGE ON SCHEMA intellicare_operacional TO operacional_user, analytics_user, intellicare_admin;
GRANT USAGE ON SCHEMA intellicare_analitico TO analytics_user, intellicare_admin;

-- Module schemas (oswaldo, florence, donabedian, etc.)
GRANT USAGE ON SCHEMA oswaldo_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA oswaldo_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA florence_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA florence_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA donabedian_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA donabedian_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA zilda_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA zilda_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA geralda_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA geralda_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA comunicacao_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA comunicacao_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA auth_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA auth_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA portal_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA portal_analitico TO analytics_user, intellicare_admin;

GRANT USAGE ON SCHEMA wanda_operacional TO operacional_user, intellicare_admin;
GRANT USAGE ON SCHEMA wanda_analitico TO analytics_user, intellicare_admin;

-- ============================================================================
-- DISPLAY SUMMARY
-- ============================================================================

\echo '=========================================='
\echo '✅ PostgreSQL Roles Created Successfully'
\echo '=========================================='
\echo 'Roles:'
\echo '  - operacional_user (transactional writes)'
\echo '  - analytics_user (read-only)'
\echo '  - intellicare_admin (full access)'
\echo '  - intellicare_app_service (service account)'
\echo ''
\echo '⚠️  IMPORTANT: Change default passwords immediately!'
\echo 'Run:'
\echo '  ALTER ROLE operacional_user WITH PASSWORD ''new_secure_password'';'
\echo '  ALTER ROLE analytics_user WITH PASSWORD ''new_secure_password'';'
\echo '  ALTER ROLE intellicare_admin WITH PASSWORD ''new_secure_password'';'
\echo ''
\echo 'Store credentials in:'
\echo '  .env files (development)'
\echo '  AWS Secrets Manager / HashiCorp Vault (production)'
\echo '=========================================='

-- List created roles
\du
