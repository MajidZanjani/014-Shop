---
quick_id: 261023-atf
status: complete
implementation_commit: 8e76c27cb4258bbe604b01437945ffaef78cdff0
---
# Supported-route customer-to-staff journey

Added mixed and support-only request/response integration scenarios with real PostgreSQL/UTF8 and enforced CSRF. Start with empty domain tables. Customer identity is created by request-code/verify routes; staff is provisioned by supported local_staff command then authenticated by password/private-code routes. All cart/request/business/attachment/review/preparation domain writes use actual API/forms. No forced login, direct domain fixture insertion or model mutation. Operator commands explicitly grant quotation and exact business scope, then revoke permission.

Flows exercise uncertain retries, Unicode partial business/helper resolution, exact attachment/review, owner safe status/document/timeline, captured assessment/retry/correction/compare, stale assessment rejection, later cart/business edits preserving retained scope, another verified owner denial, private-summary canaries, revocation and separate staff/customer logout. Country/tax remain null/deferred; all commercial actions disabled. Programmatic captures are new owned synthetic files, read only inside tests; no manual/real credential or external service access.

## Evidence

- CORE_LOCAL_PASS checks=5 tests=149 duration_seconds=37.373, PostgreSQL18.6/UTF8:139 Django tests plus10 loopback observations. Two new complete mixed/support-only journeys passed first full run. Existing147 tests remain green.
- These are Django request/response integration tests, not new live HTTP sign-in/browser/render/accessibility or production MFA/email/recovery qualification. Core lane retains ten independent loopback observations; no new actual HTTP customer/staff journey claim.
- Actual candidate source `/nix/store/l3vn73jkfwzm5clml2q9hd34rjifzhh9-shop-python-source`:117 files/fifteen templates; exact repository bytes/allowlist/no symlinks. No image/deployment acceptance.
- Planning labels now explicitly distinguish development focus7 from last fully completed1. Phases2–6 remain partial/qualification-pending under the October22 amendment. Extended guard checks both labels; four in-memory drift cases (focus, completion, machine-state and counts) reject with no files mutated. Positive planning check passes; prior frontend110/proxy1 and harness15 remain scoped to original evidence, not rerun.
- All affected live planning files reviewed/refreshed before commit. Immutable source and historical evidence preserved. Regenerate canonical state.json, run planning guard and sync after every commit. No demos, agents or async jobs remain.

## Pending scope and next action

Progress unchanged:1/14 fully completed phases (rounded7%),10/20 planned records, Phase02 remains8/18. Country/tax answers, current human/browser reviews, actual delivery/staff MFA/recovery, approved commercial inputs/acceptance/order conversion and full release gates remain pending. No FULL_PASS, hosted CI or off-host outage/recovery claim.

Next local slice: Django no-JavaScript customer access entry using existing captured verification flow, with strict CSRF/body/privacy/session handling and no real delivery or new membership scope. This addresses a remaining fallback/access prerequisite without waiting for Country/tax answers. Keep all commercial gates closed.

Implementation 8e76c27 was immediately synced to origin/main with0/0 ahead/behind. Registry completion also reconciles live planning before commit and must be immediately synced.
