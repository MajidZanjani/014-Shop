---
phase: 02-reproducible-application-and-deployment-skeleton
plan: "12"
status: qualification_pending
requires: [02-06]
provides: [versioned-health-openapi, closed-probe-schema, offline-observed-contract-checks]
requirements-completed: []
---
# Phase 2 Plan 12: Observed contracts; outage qualification pending

OpenAPI 3.1.1 describes only existing GET live/ready paths with exact closed 200/503 bodies. The closed Draft 2020-12 probe envelope validates actual CLI request and persisted worker result, including UUID format. Pinned jsonschema tools validate official metaschema, own schemas, observations and positive/negative fixtures inside a network-denied process namespace. Remote references are rejected and registry retrieval denied; no automatic fetch.

Official inert metaschema acquired from https://spec.openapis.org/oas/3.1/schema/2022-10-07 (33992 bytes, SHA-256 da01ba28852cac0de53893797cb8d1942bc3b05084f526dcc216717dec314ed0), vendored unchanged and checked before use. It is a schema artifact, not executable package installation.

Final local command `check_contracts.py --local` passed 7 checks/5 tests in 11.964 seconds. Actual new PostgreSQL, migrations, CLI enqueue/worker and loopback Gunicorn provide real healthy responses and persisted result. Rejections cover closed fields/version/status bodies, malformed UUID/schema, missing artifact and remote refs. Missing required observations cannot pass.

**Pending:** local 503 comes from the actual Django handler with a synthetic connection exception. It is not HTTP database-outage evidence. Full contracts default requires the independently assigned runner authorization for owned-synthetic-postgresql-outage, runs the prepared real HTTP outage case there and otherwise returns nonzero. No such fault or full CONTRACTS_PASS executed here. Required BUILD/phase/production acceptance remains pending. No product/price/payment contract or public API publication is claimed.
