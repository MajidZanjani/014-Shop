---
status: complete
---
# Connected Unix peer admission

Both operator paths inspect a duplicate of the actual libpq FD for Linux Unix-stream credentials, matching peer PID/UID/GID to approved postmaster/startup identities. Inspection checks before/after observation; schema checks at every connected admission. Original descriptors/protocol bytes are preserved.

Final local SQL3/114 in10.140s, source7/5 in4.362s and operator7/17 in5.995s pass. Real disposable SCRAM inspection/schema peers and wrong-PID denial pass. Real socketpair/type/descriptor controls and mocked close-before-SQL controls pass. Initial112-test pass precedes final114; no failing peer runs. New native54/9 and source-notice9/7 revisions preserve prior evidence.

SO_PEERCRED reflects listen-time identity, not current backend state; retain fresh process/start/resource/SQL guards. Fixed root/namespace/runtime/storage/socket-path and role provisioning remain unqualified. Publisher/custody/barrier, Django/app/replica, full CI/OCI and independent recovery unfinished. No real credentials/host/provider action or full phase acceptance.14/16/17 incomplete. Local commit only; remote publication remains blocked pending scoped authority.
