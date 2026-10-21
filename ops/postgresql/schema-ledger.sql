-- Review/bootstrap artifact only; no automatic creation or adoption.
-- Run only through a separately authorized, destination-guarded bootstrap path.
CREATE SCHEMA shop_control;
REVOKE ALL ON SCHEMA shop_control FROM PUBLIC;
CREATE TABLE shop_control.schema_migrations (
    migration_id text PRIMARY KEY,
    artifact_sha256 text NOT NULL,
    authorization_id text NOT NULL UNIQUE,
    applied_at timestamp with time zone NOT NULL
);
REVOKE ALL ON TABLE shop_control.schema_migrations FROM PUBLIC;
