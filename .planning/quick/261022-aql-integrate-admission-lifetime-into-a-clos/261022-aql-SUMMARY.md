---
status: complete
evidence_class: local-synthetic
---
# Django multi-statement transaction precursor

Implemented guarded_atomic for an already-connected registered Django/Psycopg wrapper. Owns a durable outer atomic transaction and holds actual admission through commit/rollback. Before/after same-connection SQL identity/durability/runtime checks, no reconnect, callback/rollback-only/manual/outer transaction acceptance or retry. Explicit twelve-module inert source package. Production backend/settings and worker call sites unchanged/closed. Initial engine-integration task narrowed after inspection: this transaction foundation is necessary before binding an application connection/role and all-write interception; it is not a qualified Django backend.

Nine new tests exercise actual Django QuerySet create/update/delete and cursor multi-statement commit/rollback, runtime/live SQL/admission changes, no reconnect, outer/manual transaction denial, callbacks/rollback-only denial and independent publisher exclusion during actual commit/rollback. Account/container and physical root path are adapted synthetic fixtures; actual owned PostgreSQL/Django/flock behavior exercised.

SQL3/18413.762s; source7/5 9.497s; operator7/17 5.951s; deployment16/31 2.292s; core-local4/22 7.710s; worker-smoke6/24 9.022s; native56/9 1.035s; notices9/7 3.820s pass. Earlier183-test run13.320s passed. Initial source/operator/deployment checks failed because new untracked module was absent from Nix Git source; git add of exact new module corrected all three. No invalid native report retained; native collected after successful runtime build. No test failure, credential/host/provider operation or production activation.

Root-bound application role/transport, all-write backend/worker integration, actual runtime/archive/recovery and14/16/17 remain pending. Expected/probe parameters remain trusted caller inputs in this precursor; docs explicitly retain that boundary.
