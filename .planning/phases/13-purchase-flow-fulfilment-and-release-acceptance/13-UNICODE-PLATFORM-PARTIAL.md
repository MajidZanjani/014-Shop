# Platform-name Unicode validation — local partial evidence

Phase13/13-01 task5,2026-10-28. Resumed from clean51f0346; preceding verified implementation73167fc. Malformed unpaired UTF-16 surrogates passed both shared validators and reached PostgreSQL JSON storage. Shared fixture/HTTP reproduction on unchanged validators ran27 tests with16 validation failures and16 database errors. The exact frontend fresh-build gate also failed the new shared malformed-name cases. These are local diagnostic failures, not actual customer/provider incidents.

Python now rejects surrogate code points in platform names. The TypeScript character class uses Unicode mode so it rejects isolated surrogates while preserving valid supplementary characters. Existing short_name errors, optional names, legacy snapshots, control-character rules,120-codepoint bounds, catalog revision and approval/offer gates remain unchanged. No normalization or silent replacement is introduced.

Thirteen new shared cases cover multilingual names, valid emoji,120/121 ASCII and supplementary-codepoint bounds, both ends of the high/low surrogate ranges, embedded/reversed surrogates and valid emoji followed by an isolated surrogate. Real PostgreSQL draft/cart HTTP tests reject invalid names with422 before any draft/cart/snapshot persists, round-trip valid Unicode and preserve exact retry identities/version1.

Focused final shop.catalog.tests/shop.catalog.cart_tests:27 tests in1.766s, no skips, system check clean. Exact frozen frontend Node24.22.0/npm11.19.1 fresh public-input build/privacy gate: FRONTEND_PASS checks=32 tests=132 duration_seconds=10.633. Full Python/TypeScript outputs agree for91 configuration and26 cart cases: CATALOG_PASS checks=117 tests=121 evidence_class=local-synthetic. Original immutable catalog revision6f538ca5eba083e0845354f740c5ce83fe5877b4409e994d5770405c5cf85b3b is unchanged.

Inert source /nix/store/p2k4iqd9q0xyg1h5vhx8rywm42w3d2k0-shop-python-source matches264 allowlisted files/33 templates/1 CSS byte for byte with no symlinks. This builds source only, not a runtime image.

## Final consolidated local verification

CORE_LOCAL_PASS checks=5 tests=588 duration_seconds=172.036; enclosing lane173.38694483193103s, failures0. The two existing120-second test batches pass with real PostgreSQL18.6/UTF8, migrations/no drift and Gunicorn route checks. PENDING_OFF_HOST database outage/recovery remains explicit. The sequential supported complete-cart demo/proxy run passes DEMO_ACCESS_PASS checks=148 aliases=2 evidence=local-synthetic-header-level. These are local synthetic checks, separate from the retained browser evidence below. No test/application/database timeout changed.

Planning/source checks pass for89 requirements/14 phases/4 immutable sources. Existing3 activity-view mutation tests and1 artifact-inventory regression pass; canonical STATE/ROADMAP/PROJECT/HANDOFF fields and all three active ROADMAP views agree. All owned test sessions exited; no async job remains.

## Reproduction

Use the unchanged frozen Nix development shells and an owned workspace TMPDIR because shared128MiB /tmp is full. Exact frontend: nix develop ./ops/nixos#default --command python3 scripts/check_frontend.py. Shared parity: same shell with python3 scripts/check_catalog.py. Focused PostgreSQL: check_worker.prepared_database()/manage migrate then manage.py test shop.catalog.tests shop.catalog.cart_tests --noinput --keepdb under the browser shell. Full backend: existing core-local lane. Retained .scratch/unicode-focused.py and /tmp/shop-dispatch-core.py use the existing /tmp/shop-ledger-wheels as the locked-wheel source; all frozen/hash/inventory/install gates remain. Local logs are .scratch/unicode-{baseline,focused,frontend-baseline,frontend,catalog,core,source}.log. No shared temporary data or Nix store was pruned.

Current retained browser224 belongs to44322c5 and precedes the commercial parser and Unicode changes; it is not promoted into a new browser run. No hosted CI, formal/manual accessibility, actual commercial/channel/provider/retention/runtime/recovery/host or production/full-phase acceptance is inferred. Remaining prerequisites are grouped in13-QUALIFICATION-REGISTER.md; task5 remains partial and no full SUMMARY is justified.
