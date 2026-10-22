---
status: complete
---
# Multi-statement Django transaction precursor

Inline GSD execution. Inspection found the existing single-DML primitive cannot wrap worker ORM atomic blocks. Implement its missing multi-statement foundation before backend activation; production engine remains closed.

1. Add runtime library guarded_atomic for an already-connected Django wrapper. No connection/credential discovery. Own outer durable atomic transaction; hold control admission through commit/rollback, validate same raw connection/autocommit/transaction state, check fresh runtime and SQL destination before/after, deny rollback-only state and deferred commit callbacks. Trusted application SQL, not sandbox or automatic ORM enforcement.
2. Real local PostgreSQL+Django tests: multi-statement commit/rollback, late identity/runtime/admission denial, nesting/manual transaction/missing connection and callbacks rejection, lease held through actual commit/rollback. Runtime/physical admission proof stays separately labelled synthetic where adapted.
3. Explicitly package source module, run SQL/source/operator/deployment/backend/worker/native checks, document precursor limits, update GSD, commit/push. Positive connection transport, all-write backend integration, role/auth rights, actual qualification and14/16/17 remain pending.
