# Plan07-02 local destination binding — partial

Implementation: pending commit; recorded base546dead. No plan/phase completion claimed.

Explicit private local destination identity and attributed intent binding are implemented; root replacement, copied/tampered markers and rebinding fail closed. Only pending/held intents exist; no claim, worker, publication service or durable worker authority exists. Retention/effect flags remain false.

Internal initialize_destination explicitly initializes only an empty owned0700 local root with caller UUID and immutable600 canonical marker. BoundPreparedArchive verifies descriptor/path device/inode and exact marker before/after each operation; reopen/exact retry preserves identity. Marker metadata explicitly denies retention/effect qualification. Existing unbound objects are never adopted or deleted.

bind_request_destination requires current exact owner or recent-MFA/private-granted staff authorization and exact retained envelope bytes. Root attestations run outside database transactions; binding commits atomically with protected destination/actor/time/MFA references. Exact retries retain original attribution and held state; competing roots cannot rebind or leave orphan database rows. Post-commit attestation/permission failures preserve binding and deny acknowledgement. This is historical attribution, not durable worker authority.

Evidence: 214 core-local tests (200 Django plus14 Gunicorn observations),46.154s; owned PostgreSQL18.6/UTF8. Actual Nix source141 files19 templates, byte-identical/allowlisted/no symlinks. Ten new tests cover identity/reopen/replacement, tamper/modes/symlinks, fsync uncertainty/retry, competing PostgreSQL bindings, holds, staff revocation during I/O and database constraints. Migration0009 application/no-drift passes. Artifact /nix/store/cdazns37s96l07sap20scgjzdqaym0il-shop-python-source. Same-agent verification; frontend/proxy unchanged and not rerun. No provider/off-host/production qualification.

Migration0009 is additive with nullable intent binding fields, protected destination/actor references and paired-field/profile/root uniqueness constraints. No backfill. Reverse only on an empty disposable database; preserve populated evidence and protected records during rollback. Production gate remains closed.

Next: Define durable archive authority and fenced local claims before publication; preserve holds and retained bytes. Country/tax and commercial effects remain gated.
