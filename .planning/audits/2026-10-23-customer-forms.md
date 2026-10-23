# Local customer forms audit — 2026-10-23

Scope: access a7d085f, owner history120f0a5, saved cart691ce9f and deliberate quotation capture74b6083. Inline source/request-boundary review under GSD audit-fix; no subagents or external operations. GSD audit-uat query reports zero structured items, which is not full UAT/phase acceptance. Existing Phase01/02 verification and external/human qualification remain unchanged.

| ID | Finding | Severity | Classification | Status |
|---|---|---|---|---|
| F-01 | Parent cart ownership read followed by snapshot read without owner recheck in cart API/editor and quotation preview | medium | auto-fixable; concrete queries and deterministic PostgreSQL regression | fixed83e8464; quick261023-cyg |

Reviewed shared single-use access, local/fake gates, strict form fields/body/methods/query parsing, session/CSRF rotation, current/historical cart commands, owner cursors, snapshot/key lock/retry arbitration, closed review projections, fixed redirects, template escaping and private headers. Existing/new request-response tests cover those boundaries. No other concrete source finding identified in this scoped review; this is not independent browser/security certification.

Country/tax, real mail/HTTPS/contact roles/staff MFA, source/legal approval, browser/accessibility/history behavior, off-host recovery, runtime/host and production gates remain pending. No authority inferred; no new external requests needed.

Evidence: pre-fix controlled ownership change returned200 on /purchase/cart/. After owner-qualified snapshot reads, the same test checks safe404 across cart editor, quotation preview and cart API. CORE_LOCAL_PASS checks5 tests178 duration40.556s (164 Django plus14 transport observations). Actual source129 files19 templates exact at /nix/store/qx34k0a9m91wvmcq2xpf70paw2bab92l-shop-python-source. Existing exact replay and API/form concurrency tests pass. No full UAT/independent security certification or phase completion claimed.
