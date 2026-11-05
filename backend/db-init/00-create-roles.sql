\set ON_ERROR_STOP on

\getenv database_name POSTGRES_DB

SELECT format('CREATE ROLE %I NOLOGIN', role_name)
FROM (VALUES ('medisync_runtime'), ('medisync_migrator'), ('medisync_cleanup')) AS roles(role_name)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE pg_roles.rolname = roles.role_name);
\gexec

GRANT CONNECT ON DATABASE :"database_name"
    TO medisync_runtime, medisync_migrator, medisync_cleanup;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO medisync_runtime, medisync_migrator, medisync_cleanup;
GRANT CREATE ON SCHEMA public TO medisync_migrator;

ALTER DEFAULT PRIVILEGES FOR ROLE medisync_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO medisync_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE medisync_migrator IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO medisync_runtime;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO medisync_runtime;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO medisync_runtime;
