"""Fixed restricted-login SQL observer; no connection, installation or live grants.

Only the two privileged cluster fields use a pinned SECURITY DEFINER function.
Role/session/endpoint/durability remain observed as the actual caller. An approved
non-application owner and separately qualified admission/transport are required.
"""
import re
import database
from guard import require

BODY = "\nSELECT c.system_identifier::pg_catalog.text, pg_catalog.current_setting('data_directory')\nFROM pg_catalog.pg_control_system() AS c\n"

POLICY_SQL = """SELECT owner.rolname, p.prosrc, p.proconfig,
    p.prokind='f' AND lang.lanname='sql' AND p.pronargs=0
    AND p.pronargdefaults=0 AND p.provariadic=0 AND p.prosupport=0
    AND p.prosecdef AND NOT p.proleakproof AND p.proretset
    AND p.provolatile='s' AND p.proparallel='r'
    AND p.prorettype='pg_catalog.record'::pg_catalog.regtype
    AND p.proallargtypes::pg_catalog.text='{25,25}' AND p.proargmodes::pg_catalog.text='{t,t}'
    AND p.proargnames=ARRAY['system_identifier','pgdata']::pg_catalog.text[]
    AND n.nspowner=p.proowner AND p.proowner<>actor.oid
    AND actor.rolcanlogin AND NOT actor.rolsuper AND NOT actor.rolcreatedb
    AND NOT actor.rolcreaterole AND NOT actor.rolreplication AND NOT actor.rolbypassrls
    AND current_user=session_user
    AND NOT EXISTS (SELECT FROM pg_catalog.pg_auth_members m WHERE m.member=actor.oid)
    AND NOT EXISTS (SELECT FROM pg_catalog.pg_database d
                    WHERE d.datname=pg_catalog.current_database() AND d.datdba=actor.oid)
    AND NOT pg_catalog.has_schema_privilege(current_user,'public','CREATE')
    AND pg_catalog.has_schema_privilege(current_user,n.oid,'USAGE')
    AND pg_catalog.has_function_privilege(current_user,p.oid,'EXECUTE')
    AND NOT EXISTS (SELECT FROM pg_catalog.aclexplode(COALESCE(p.proacl,
        pg_catalog.acldefault('f',p.proowner))) a WHERE a.grantee<>p.proowner
        AND (a.grantee<>actor.oid OR a.privilege_type<>'EXECUTE' OR a.is_grantable
             OR a.grantor<>p.proowner))
    AND NOT EXISTS (SELECT FROM pg_catalog.aclexplode(COALESCE(n.nspacl,
        pg_catalog.acldefault('n',n.nspowner))) a WHERE a.grantee<>n.nspowner
        AND (a.grantee<>actor.oid OR a.privilege_type<>'USAGE' OR a.is_grantable
             OR a.grantor<>n.nspowner))
    FROM pg_catalog.pg_proc p
    JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace
    JOIN pg_catalog.pg_roles owner ON owner.oid=p.proowner
    JOIN pg_catalog.pg_roles actor ON actor.rolname=current_user
    JOIN pg_catalog.pg_language lang ON lang.oid=p.prolang
    WHERE n.nspname='shop_runtime' AND p.proname='database_identity_v1'"""

APPLICATION_IDENTITY_SQL = """SELECT identity.system_identifier, identity.pgdata,
    pg_catalog.current_database(), current_user, session_user,
    pg_catalog.inet_server_addr()::pg_catalog.text, pg_catalog.inet_server_port(),
    pg_catalog.current_setting('port')::integer,
    pg_catalog.current_setting('fsync'), pg_catalog.current_setting('synchronous_commit'),
    pg_catalog.current_setting('data_checksums'), pg_catalog.pg_is_in_recovery()
    FROM shop_runtime.database_identity_v1() AS identity"""


def observe_application_database(cursor, runtime, observer_owner):
    """Read exact same-connection identity under a restricted application login.

    observer_owner must come from separately approved immutable policy, never a
    caller request. No PUBLIC/membership/broad role fallback or object adoption.
    The owner/admin must cooperate with the transaction's admission lease; this
    cannot prevent a privileged noncooperating catalog change between queries.
    """
    require(type(observer_owner) is str and re.fullmatch(r'[a-z_][a-z0-9_]{0,62}',observer_owner))
    cursor.execute(POLICY_SQL,prepare=True)
    rows=cursor.fetchall()
    require(rows == [(observer_owner,BODY,['search_path=pg_catalog, pg_temp'],True)])
    cursor.execute(APPLICATION_IDENTITY_SQL,prepare=True)
    rows=cursor.fetchall()
    require(len(rows)==1)
    return database.identity_from_row(rows[0],runtime)
