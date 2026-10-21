---
status: complete
---
# Actual local SCRAM operator inspection

Code908195a adds actual disposable PostgreSQL18.6 SCRAM authentication through operator_inspect.inspect_from_fds and the actual guarded read-only ledger inspector. Three connections observe not_recorded/recorded/conflict, return retry/reopening=false, leave ledger rows unchanged and close. All use default read-only sessions and an attempted DELETE is rejected. A wrong synthetic password is rejected without retry. The real private FD reader executes through test descriptor mapping. Only the new token-owned scratch cluster's HBA/password are changed; existing services and allocations unchanged.

Local database-destination passed3 checks/82 tests,8.657s after final read-only denial assertion. Earlier first run failed fixture prevalidation of expected==expected; corrected explicit scratch-path adaptation. Second failed fixture insert omitted required applied_at; supplied clock_timestamp(). Intermediate82-test run passed8.662s before final assertion. These are fixture corrections, not production runtime fixes. No other lanes rerun because runtime/package bytes are unchanged. No full all/FULL_PASS or operational qualification.

Socket/PGDATA paths, root records, effective operator UID, process probe and socket ancestry/identity are explicitly adapted/mocked. Uses fixture administrative role, not qualified least-privilege access. Actual fixed FD0/FD3 launcher, positive peer/container/process binding, root-record issuer/publisher/admission barrier, production socket/HBA/roles, Django writes/migrations, generator/replica/image/notices/CI and off-host qualification remain pending. No .env read, actual credential needed, host access, protected-service change or purchase. Phase02/14/16/17 remain incomplete; runner unassigned with no repeated request.

Bounded quick task complete; larger implementation and qualification remain incomplete. git diff --check passed.
