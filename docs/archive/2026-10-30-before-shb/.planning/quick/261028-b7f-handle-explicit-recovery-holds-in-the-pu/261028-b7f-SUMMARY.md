---
status: complete
implementation_commit: db56df35b1f979f8bc21d9a686712c9d419b5fd9
requirements: [OPS-02, AUTH-01, UAT-03]
evidence_class: local-synthetic
actual_recovery_qualified: false
---
# Public recovery response and late-response fence

Completed the three tasks inline. Original transport/real-React baseline3 failures and intermediate late-rebase2 failures are retained. A fixed recovery503 header clears client private/context state with manual recovery guidance; arbitrary error bodies remain unread. An opaque module-only generation fences older responses before/after JSON, including old session rebases and same-context reconnect. Ordinary503/network exact retries, current CSRF/context/resource authority and no persistence/automatic POST retry remain.

Final focused backend63 tests17.811s, exact frontend137 tests/32 checks10.769s, catalog117/121, fresh browser227 and13 report/controller/public tests pass. Backend624/5 and proxy148/2 retain0f4a063 pre-header scope. Exact source /nix/store/kxjilvd16zhhg9ap7r5j87hd6qf4mj7k-shop-python-source:272 files/33 templates/1 CSS/no symlinks. [Evidence/diagnostics](../../phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-RECOVERY-PARTIAL.md).

## Self-Check: PASSED

Local scope passes. The browser503 is a controlled response simulation, with read-only confirmation that it did not mutate server access; actual recovery/full acceptance remains pending. Next independent design is restore-startup quarantine for a restored unheld epoch. Commercial inputs remain pending. No external/protected operation or new dependency.
