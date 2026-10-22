---
status: complete
---
# Schema role admission enforcement

The separate schema command now rejects privileged attributes, database ownership, indirect/extra role memberships and membership administration after connecting and at each existing admission point. Only pg_read_all_settings membership is permitted. No provisioning or mutation of roles is supplied.

Real PostgreSQL and SCRAM evidence covers attribute/membership/ownership denials, complete role apply/replay, and a CREATEDB promotion after DDL that triggers rollback at the next check. Synthetic denial confirms close-before-mutation. Final database-destination3 checks/110 tests10.010s; source7/5 in4.251s; operator7/17 in5.503s; deployment16/31 in2.210s pass. Native54/9 and source-notices9/7 write passes retain new content-addressed evidence. No failing enforcement run; initial109-test passes precede the final110-test run.

The predicate does not attest every direct privilege, routine or historical owner. Actual runtime/roles/socket/custody/publisher/Django/independent recovery and14/16/17/full phase remain pending. No credentials/host/provider action. Commit local only; remote publication remains separately blocked.
