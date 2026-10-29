-- Candidate source only; installation and role grants require separate authority.
BEGIN;
SET LOCAL search_path = pg_catalog;
CREATE SCHEMA shop_runtime;
REVOKE ALL ON SCHEMA shop_runtime FROM PUBLIC;
CREATE FUNCTION shop_runtime.database_identity_v1()
RETURNS TABLE(system_identifier pg_catalog.text, pgdata pg_catalog.text)
LANGUAGE sql STABLE SECURITY DEFINER PARALLEL RESTRICTED
SET search_path = pg_catalog, pg_temp
AS $shop_identity$
SELECT c.system_identifier::pg_catalog.text, pg_catalog.current_setting('data_directory')
FROM pg_catalog.pg_control_system() AS c
$shop_identity$;
REVOKE ALL ON FUNCTION shop_runtime.database_identity_v1() FROM PUBLIC;
COMMIT;
