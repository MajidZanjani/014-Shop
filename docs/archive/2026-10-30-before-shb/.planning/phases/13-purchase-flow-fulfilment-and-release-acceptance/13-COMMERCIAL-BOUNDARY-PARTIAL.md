# Commercial revision boundary — local partial evidence

Phase13/13-01 task5, 2026-10-27. Malformed nonfinite, oversized integer, deeply nested and corrupted in-memory revision values now raise fixed CommercialRevisionError codes. Trusted approval-verifier exceptions hold as protected_approval_required, once without retry; the synthetic path never calls that verifier. Valid immutable snapshots and all actual approval gates remain unchanged.

Focused baseline44 failed with7 errors. Final focused46 real-PostgreSQL consumer/checkout/payment tests pass in5.229s. Full CORE_LOCAL_PASS checks=5 tests=584 duration_seconds=171.536 (enclosing172.853s). DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level passes with the supported complete-cart fixture. Limits remain120-second batches/900-second outer; off-host database outage/recovery remains unexecuted.

Current inert source /nix/store/wv8fc6vq5d8xw4krl26ifpqh9p1rh65c-shop-python-source matches264 files/33 templates/1 CSS byte-for-byte, no symlinks. Retained exact frontend/browser224 evidence belongs to44322c5 before this Python-only change; unchanged frontend checks were not repeated. No hosted CI, formal/manual acceptance, actual commercial/provider, host or production qualification is inferred.

## Next task saved for resume

Pure local diagnostic, not a reproduced database/API failure: backend rules.evaluate accepts platform {'choice':'other-board','kit_id':None,'name':chr(0xd800)} in an otherwise valid frontend/tests/conformance.json fixture (lone_surrogate_accepted=True). frontend/src/lib/configuration.ts uses the analogous control-character-only check. Reproduce through shared conformance and real PostgreSQL draft/cart HTTP tests; reject unpaired surrogates in backend/shop/catalog/rules.py and the TypeScript validator while preserving valid Unicode/emoji and the120-codepoint bound. No Unicode implementation edits were made in this step. User explicitly requested pause after the current commercial step.
