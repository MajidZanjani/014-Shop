# Local development

Current requirements and next tasks: [.planning/STATE.md](../.planning/STATE.md), [ROADMAP.md](../.planning/ROADMAP.md), [final purchase-flow amendment](../.planning/PURCHASE-FLOW-AMENDMENT.md). Earlier per-task status/next-step narratives are retained in the dated pre-amendment archive and are not active instructions.

Use the pinned `ops/nixos` development shell. Existing `.env` contents are not loaded by the application or ordinary synthetic tests; do not print/copy secrets into build inputs, logs or evidence. Local/synthetic fake bank/mail/storage only. Actual destination/runtime/production qualification remains pending.

- `nix develop --max-jobs 1 --cores 4 ./ops/nixos#backend --command python3 scripts/demo_purchase_flow.py` — fresh-owned-PostgreSQL minimal platform/standard-offer/staged-delivery rehearsal; see [scope and live gaps](purchase-flow.md).
- `nix develop --max-jobs 1 --cores 4 ./ops/nixos#backend --command python3 scripts/check_backend.py core-local` — owned PostgreSQL migrations/no drift, Django and loopback Gunicorn checks; no off-host outage/recovery claim.
- `nix develop --max-jobs 1 --cores 4 ./ops/nixos --command python3 scripts/check_frontend.py` — allowlisted static build, installed-graph checks and public/privacy/runtime boundaries.
- `python3 scripts/check_planning.py` and `python3 scripts/check_purchase_plan.py --refresh-inventory` — canonical phase/requirement/source reconciliation.

The existing disposable backend demo (`scripts/demo.py --backend`, see `--help`) supplies local customer access, saved cart/quotation/business and staff rehearsal paths. Use synthetic `.invalid` addresses and the privately captured-code procedure. No real messages are sent. `/purchase/access/`, `/purchase/simple/`, `/purchase/cart/`, `/purchase/request-quotation/`, owner quotation/business/document/history paths preserve strict CSRF and resource permissions. Staff rehearsal is separate and does not qualify real MFA.

Prepared archive work: [local operator runbook](local-prepared-archive.md). Payment uncertainty/holds/read-only recovery: [synthetic bank](synthetic-bank.md). Prepared bytes and simulated completion never authorize actual commerce. Before every commit reconcile current planning, publish state.json, run planning checks and sync without force. Preserve all source/evidence/qualified dependency bytes and existing protected services.
