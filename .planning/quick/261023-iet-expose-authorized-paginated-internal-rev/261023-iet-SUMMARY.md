---
quick_id: 261023-iet
status: complete
implementation_commit: 9039679
---
# Complete assigned internal review history

Staff can browse all retained internal review decisions through stable20-row HTML/JSON history with original reviewer attribution. The route shares the existing committed review-counter queryset, parent assignment/consistency and canonical bounded version cursor; it omits private digests, business values and MFA evidence, including after a private-business grant is withdrawn. CORE_LOCAL_PASS5 checks/288 tests (274 Django plus14 Gunicorn),77.696s; exact source /nix/store/7f161hk8xg4anvmxhwlygvzgvd8fg2np-shop-python-source168 files23 templates/no symlinks. No migration/commercial effect.

GET /staff/quotation-requests/<UUID>/reviews/history/ follows the existing request summary permission: current recent staff MFA and exact parent assignment authorize decision/scope/reviewer/time metadata, never private business values, digests or MFA evidence. Current positive business grants remain necessary for private details/review writes. The new route never grants or widens them. Original review records remain immutable by API.

Shared history_rows preserves the retained parent review counter for both existing20-row summary and all older pages. Preparation/review history share before_version; current UUID queue pagination is unchanged. No-JS request-screen link and older/newest controls make corrections older than20 reachable.

## Verification

Five new tests create decisions through actual local staff login/review operations, including23-decision pagination/new correction, another actually authenticated reviewer with explicit operator assignment, safe metadata after private-business revocation, SQL no-write/output checks, strict cursors/parent consistency/method/mode/MFA/grant denial, and separate-connection supported correction after parent lookup. The initial test patch landed at a repeated assertion inside the preceding class and used a second cart for an already unique owner; corrected class placement and separate-owner fixture, then AST asserted class test counts4/4/5. Failed run is not evidence. Corrected focused31 Django plus14 Gunicorn=45 tests18.675s passes. Final full288/77.696s passes; PostgreSQL18.6/UTF8,0012 migration application/no drift and exact168-file23-template/no-symlink source pass. No skipped tests or migrations; frontend/proxy unchanged/not rerun. No production/real-MFA/provider/off-host/recovery acceptance.

Next: Implement the independent typed local-synthetic bank-adapter boundary and durable fake-provider observations: explicit synthetic-only capabilities, exact merchant/currency/amount/reference correlation, key/reference idempotency and lookup after a timeout occurring after the fake operation commits. Keep worker Probe/FakeReceipt unchanged; no approved order, real-bank capability, financial confirmation, entitlement or dispatch authorization is inferred. SourceT07 permits synthetic flows while live tax/legal values remain pending. Continue across commits without routine context pauses.
