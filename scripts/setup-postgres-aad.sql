-- Run as Postgres AAD admin (ActiveDirectory admin) after AAD is enabled.
-- Adjust role names to match deployed managed identities or Entra groups.

-- App RW role for backend/worker MI
CREATE ROLE "engram_app_rw" WITH LOGIN;
GRANT CONNECT ON DATABASE engram TO "engram_app_rw";
GRANT USAGE ON SCHEMA public TO "engram_app_rw";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "engram_app_rw";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "engram_app_rw";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO "engram_app_rw";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO "engram_app_rw";

-- Read-only role (analytics)
CREATE ROLE "engram_readonly" WITH LOGIN;
GRANT CONNECT ON DATABASE engram TO "engram_readonly";
GRANT USAGE ON SCHEMA public TO "engram_readonly";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "engram_readonly";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "engram_readonly";

-- Map managed identities (replace with actual AAD object IDs)
-- Example: CREATE USER "api-mi" FROM EXTERNAL PROVIDER;
-- ALTER ROLE "api-mi" WITH INHERIT;
-- GRANT "engram_app_rw" TO "api-mi";

-- Example for worker MI:
-- CREATE USER "worker-mi" FROM EXTERNAL PROVIDER;
-- ALTER ROLE "worker-mi" WITH INHERIT;
-- GRANT "engram_app_rw" TO "worker-mi";

-- Rotate grants if schemas change; rerun after migrations that add schemas.
-- Setup AAD roles for Engram Postgres
-- Run with an AAD admin context after enabling AAD authentication.

-- Create roles for managed identities (replace object ids with real GUIDs if using AAD auth directly)
-- Example principals:
--   engram-backend-identity
--   engram-worker-identity

-- App read/write role
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') THEN
    CREATE ROLE app_rw;
  END IF;
END $$;

-- Analytics read-only role
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'analytics_ro') THEN
    CREATE ROLE analytics_ro;
  END IF;
END $$;

-- Grant privileges (public schema example)
GRANT CONNECT ON DATABASE engram TO app_rw;
GRANT USAGE ON SCHEMA public TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;

GRANT CONNECT ON DATABASE engram TO analytics_ro;
GRANT USAGE ON SCHEMA public TO analytics_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_ro;

-- Map AAD roles/users (replace with actual role names assigned in AAD)
-- Example: CREATE ROLE "engram-backend-mi" WITH LOGIN IN ROLE app_rw;
-- Example: CREATE ROLE "engram-worker-mi" WITH LOGIN IN ROLE app_rw;
-- PostgreSQL AAD setup for Engram
-- Run with an AAD admin on the server (after AAD integration is enabled).

-- Map Managed Identities (replace with actual MI object IDs)
-- Example: CREATE ROLE "engram-backend-identity" WITH LOGIN INHERIT;

CREATE ROLE "engram-backend-identity" WITH LOGIN INHERIT;
CREATE ROLE "engram-worker-identity" WITH LOGIN INHERIT;

-- Application roles
CREATE ROLE app_rw NOINHERIT;
CREATE ROLE analytics_ro NOINHERIT;

-- Grant to MI roles
GRANT app_rw TO "engram-backend-identity";
GRANT app_rw TO "engram-worker-identity";

-- Schema/data grants
GRANT USAGE ON SCHEMA public TO app_rw;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;

-- Read-only role for analytics
GRANT USAGE ON SCHEMA public TO analytics_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO analytics_ro;

-- Optional: revoke wide public privileges
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
-- Assign AAD principals to database roles after AAD auth is enabled.
-- Replace placeholders with actual AAD object IDs mapped through Azure AD authentication.

-- Backend/worker Managed Identity (objectId)
CREATE ROLE "engram-backend-identity" WITH LOGIN INHERIT;
GRANT CONNECT ON DATABASE engram TO "engram-backend-identity";
GRANT USAGE ON SCHEMA public TO "engram-backend-identity";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "engram-backend-identity";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "engram-backend-identity";

-- Analytics read-only (optional)
CREATE ROLE "engram-analytics-ro" WITH LOGIN INHERIT;
GRANT CONNECT ON DATABASE engram TO "engram-analytics-ro";
GRANT USAGE ON SCHEMA public TO "engram-analytics-ro";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "engram-analytics-ro";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "engram-analytics-ro";

