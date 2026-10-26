---
status: complete
---
# Read-only recovery tooling

Added inspect_synthetic_payment with closed metadata output and fixed command errors. Four actual-process tests cover safe state reports, no writes, malformed/unknown IDs, early startup refusals and database lock timeout. Existing startup gate retains its original separate error boundary.

Full integrated core-local319 tests/5 checks,86.218s; PostgreSQL18.6/UTF8 and migrations/no drift pass. Source184 exact files/23 templates/no symlinks. Evidence: [.planning lifecycle partial](../../phases/08-payment-domain-and-fault-injectable-fake-bank/08-LIFECYCLE-PARTIAL.md). No full phase or live financial acceptance.
