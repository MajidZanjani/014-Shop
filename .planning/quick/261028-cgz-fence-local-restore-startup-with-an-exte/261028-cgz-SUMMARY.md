---
status: complete
implementation_commit: 35f02017558114d2c5d2a48f7eb88920775894ad
requirements: [OPS-02, UAT-03]
evidence_class: local-synthetic
actual_recovery_qualified: false
---

# Local restore startup identity fence

Completed the three tasks inline under GSD quick. A real pre-fix unheld-session exposure failed; a fresh external fake-only restore identity now closes access/authentication/new effects until matching immutable quarantine/release history exists and the current epoch is unheld. Missing epoch remains closed. Separate cooperating processes recognize the persisted sequence, while later holds, release/drain checks, fresh authentication and read-only bank lookup retain their behavior.

Final focused89 tests25.554s and current backend637 tests/5 checks199.598s (outer201.077s) pass with original bounds. No migration drift. Exact274-file inert source `/nix/store/kqw59vdg9sfxk7hw7a8pv2wabjbfjwsk-shop-python-source`:33 templates/1 CSS/no symlinks. [Evidence, diagnostic assertion and remaining gates](../../phases/13-purchase-flow-fulfilment-and-release-acceptance/13-STARTUP-RECOVERY-PARTIAL.md). Local configuration and selection limits are documented in `docs/local-recovery.md`; examples contain no reused startup identity.

## Self-Check: PASSED

Local scope only. Actual isolation, complete-loss restoration, post-point revocations/MFA reconciliation and full acceptance remain pending. No external API, production recovery control, protected mutation or approval inferred. Commercial inputs remain pending by user instruction. Continue to the concrete local post-point resource-revocation review after ordinary commit/push.
