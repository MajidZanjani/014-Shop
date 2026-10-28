---
status: complete
requirements: [OPS-02, PAY-03, BANK-03, UAT-03]
evidence_class: local-synthetic
actual_recovery_qualified: false
---
# Local recovery effect admission and drain

Completed the three scoped tasks inline: durable serialized admission/one-way exit history; worker/claim/payment/finance/direct fake-bank and statement/inbox boundaries; real PostgreSQL race/fault/migration/integration verification. Quarantine closes new admission but honestly reports already admitted work until its exit commits. Synthetic release refuses every unfinished record, including process/exit failure and older epochs. No expiry, automatic clear or financial retry authority is introduced. Pure idle worker polling does not accumulate admissions.

Read-only typed lookup, internal attempt reconciliation and existing captured-mail acknowledgement remain available; worker inbox processing pauses. Nested bank admission checks a quarantine after an archived one-way claim, leaving uncertainty lookup-only. Staff access remains denied while held. No DB lock/transaction spans external adapter execution; this is not actual process/egress isolation, provider reconciliation or safe reopening.

Verification:112 focused PostgreSQL tests32.022s; CORE_LOCAL_PASS618 tests/5 checks188.360s (outer189.778s); WORKER_LOCAL_PASS24 tests/6 checks13.258s including rejected broken-control mutations; network-isolated ADAPTERS_PASS6 tests/3 checks8.067s; supported complete-cart/MFA/proxy148 checks/2 loopback aliases. Migration0006/no drift; exact source /nix/store/bl72abmks8z0kv0ga31agp73jhbmkbsp-shop-python-source:270 files/33 templates/1 CSS/no symlinks. [Detailed evidence](../../phases/13-purchase-flow-fulfilment-and-release-acceptance/13-RECOVERY-EFFECTS-PARTIAL.md).

The initial optional isolated adapter producer passed all six assertions but failed Django DROP DATABASE at the unchanged one-second statement timeout. Diagnostic output is retained. The producer now uses --keepdb like the other local lanes; its owned outer cluster still cleans up. Corrected complete producer passes with unchanged45-second test/120-second enclosing adapter bounds. No shared cleanup, new dependency or actual/protected operation.

## Self-Check: PASSED

Scoped local acceptance passes. Actual recovery/full Phase13 acceptance remains pending, as do commercial inputs by user instruction. Continue across commit/push to the concrete sign-in/challenge/quarantine overlap risk; no additional human approval is needed for local work.
