# SLL xSPI-MC Shop

## What This Is

A configurable xSPI-MC semiconductor-IP shop at `shop.xspi.pro` for engineering and business purchasers. Customers configure vendor-specific licences, answer one basic board/platform question, buy applicable pre-approved standard offers or request a narrow exception quote, and purchase non-expiring ten-hour SLL support independently or with IP. Approved R&D materials may precede a promised later reference design. Staff use MFA-protected workflows to review acceptance/payment, issue matching private packages and keys, process renewal/rehosting cases, and account for support work.

## Current implementation status — 2026-10-28

**Current development focus:** 13 — purchase-flow, fulfilment and release acceptance; verified Phase8/10/12 local slices retained with actual acceptance pending. [Current purchase-flow authority](PURCHASE-FLOW-AMENDMENT.md).

**Current plan:** 13-01 — Eight final purchase-flow acceptance cases.

**Execution status:** in progress — configuration-draft recovery fence verified locally (focused135, backend726/5, proxy148/2, source276); actual/full acceptance pending.

**Next implementation task:** Start a new GSD quick task and reproduce quotation JSON/native POST recovery overlap before capture_quotation, then inspect its private list/detail/capture-page reads. Keep company commercial and actual inputs pending without re-asking.

Configuration-draft list/get/save and private retry payloads now require their originating epoch before queries. [Current evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-DRAFT-RECOVERY-PARTIAL.md). Original10-test/13-failure control, fixed focused135/26.803s, current backend726/5/229.455s, supported demo/proxy148/2 and exact276-file source pass. Cart/checkout/support/recovery evidence retains its scope; actual/company inputs remain pending.

Before every commit reconcile affected current references, publish state.json and run python3 scripts/check_planning.py. Sync commits to origin/main without force. Historical evidence retains its original scope.

## Core Value

Turn an exact approved standard or reviewed xSPI-MC configuration or support purchase into attributable acceptance, verified payment and recoverable licence delivery or support credit without duplicate effects.

## Business Context

- **Customer:** Business/professional engineering purchasers and their explicitly authorized purchasing, invoice and technical contacts.
- **Revenue model:** Reviewed annual/perpetual IP licence scopes plus separately purchased ten-hour support packages; hosted payments of approved direct or quoted orders.
- **Success metric:** Verified end-to-end purchase/delivery and support usage journeys with reconstructable evidence and no duplicate financial, licence or ledger effects; no sales target supplied.
- **Strategy notes:** October 21 proposal and handoff, identified in SOURCES.md; P-10 hosting direction is selected, with qualification and other commercial/operating inputs pending.

## Requirements

### Validated

- ✓ Exact source preservation and complete option/field/declaration traceability — Phase 1, automated checks and four explicit human review responses. This validates documentation only; no application or deployed system acceptance is claimed.

### Active

- [ ] Compile strict, immutable Markdown catalogs with matching browser/backend rules and approval gates.
- [ ] Provide accessible static configuration, private host editing, multi-line quotes and line-type-aware checkout.
- [ ] Preserve exact acceptance, totals and payment identities across retries, races and crashes.
- [ ] Deliver approved encrypted RTL/manual/reference design/key packages through private resource grants.
- [ ] Sell support-only top-ups and account for non-expiring credits, reservations, work and statements durably.
- [ ] Prepare isolated publication, DNS/TLS, backup, restore and operational handover with honest external gates.

Detailed testable scope and phase mapping: REQUIREMENTS.md and ROADMAP.md. The final26October revision2 amendment controls the changed purchase/support/staged-delivery requirements; the original handoff remains normative elsewhere.

### Out of Scope

A compulsory engineering-case/upload portal, comprehensive hardware database, technical checkout questionnaire, new general workflow engine, automated cross-project credit pooling, unrelated third-party-IP/general consultancy products, automatic recurring debits, a general organization-account portal, automatic proprietary key generation, FPGA synthesis/build services, broad marketing campaigns, website migration, and changes to existing production services are excluded by the new source. No additional products, vendors, invented trial form or country/tax options are imported from earlier plans.

## Context

Replanned on 2026-10-21 from the complete protected-services proposal/handoff. The exact historical product bytes remain unchanged; final26October revision2 changes the specific purchase/support/delivery requirements recorded in PURCHASE-FLOW-AMENDMENT.md. Earlier planning is archived outside active planning; retained development evidence is reviewed for applicability rather than credited by task number. The original reset was documentation-only. The 2026-10-22 execution amendment now authorizes local repository implementation and ordinary isolated tests; external operations retain scoped authority gates.

Retain the existing authorized workflow preferences (autonomous planning, fine granularity, independent parallel work, documentation commits/sync and current-model inheritance). This planning pass is performed inline. Use supplied research as dated input; exact dependencies, tariffs, account capabilities and legal/merchant facts are verified at their affected phases. No live external audit or application tests are claimed.

## Constraints

- **Architecture:** Static Astro Content Collections + selected React islands; Django LTS/Gunicorn + PostgreSQL and one leased database outbox worker; Django owns `/purchase/simple/`. No request-time Astro/Node service or mandatory Redis/Celery/CMS/IdP.
- **Authority:** `SLL_xSPI_MC_Product_Page.md` embedded in the October21 proposal is the immutable baseline; final26October purchase-flow revision2 supersedes conflicting purchase/support/staged-delivery requirements. One Markdown/YAML catalog compiles immutable public/private revisions; protected approvals govern offers. Admin cannot create a competing catalog.
- **Product:** `sll-xspi-mc`, `sll-xspi-mc-support-10h`, profile `sll-xspi-mc-v1`; exactly three vendors and thirteen ordered families. One vendor and quantity one per configured IP line; support has real positive package quantity.
- **Rights and money:** RDP is Altera-only; higher volume requires quotation. EUR is draft display/collection intent. Unknown rates, recurrence, coverage, rights, access or terms remain null/pending and disable affected live offers. Five-plus-five allowances and €50 are provisional; no universal MAC rule.
- **Private data:** Encrypt/version host bindings, mask ordinary summaries, and authorize each resource. Keep raw host IDs/keys, business/tax details and bearer links out of public artifacts, URLs, ordinary logs and browser persistence. Staff MFA covers every privileged route.
- **Durability:** Archive recoverable snapshots before bank dispatch, document issue, delivery activation, support-credit spendability and chargeable work; archive actual support completion before final statement publication. Prepared evidence is not completion. An uncertain bank operation cannot authorize a blind retry.
- **Purchase flow:** One platform question plus conditional kit/name; unknown/custom/unfinished boards may use an applicable pre-approved development offer. Support optional/required and approved minimum come from the offer; no universal mandatory package, per-sale engineering approval, technical dossier or portal. Later reference design remains an explicit obligation.
- **Support:** SLL IP/integration guidance only. Each paid/accepted package grants exactly 36,000 integer seconds once with no expiry. Reservations prevent competing spend; corrections reverse/replace; statements use committed ledger revisions. Support never renews IP rights.
- **Infrastructure:** Existing OVH dedicated host `mx1`; NixOS-declared rootless Podman Quadlet/user-systemd under new proposed `shopsvc`, directly on the host, outside `claude-dev`. Separate Django, one worker, new shop PostgreSQL cluster and internal Caddy containers; independently owned backup jobs. No new production compute/block/IP rental or automatic paid fallback.
- **Domains:** Customer `https://shop.xspi.pro`; proposed staff `https://shop-admin.xspi.pro`; Route 53 authority unverified. Existing public ingress/TLS stays unchanged: prove a complete existing route/certificate lifecycle or defer activation with exact service/action proposal. Only later explicit service/action authorization can permit a protected change. New shop issuer is Let’s Encrypt; conditional DNS-01 cannot supply a missing traffic path. No A/AAAA before end-to-end path proof.
- **Recovery:** Independent off-host complete-pool-loss rehearsal, without production rpool or host-only secrets. Five-minute WAL timeout, 35-day DB window, 15-minute DB RPO and four-hour operator-start technical restore are proposed targets; include target provisioning/traffic timing and measure safe reopening separately. Block effects before exposure; reconcile money/acceptance/documents/licences/support and invalidate restored access/MFA state.
- **Evidence:** Real PostgreSQL for concurrency; label local/synthetic, selected-bank sandbox, actual OVH and production evidence separately. No invented approvals, compatibility, legal or provider guarantees.
- **Authorization:** The 2026-10-22 execution amendment authorizes local repository implementation and ordinary isolated tests; deployment and external operations retain their separate scoped gates. Source deployment designs do not grant host access or a protected-service exception. Real mail, bank, DNS/certificates, allowed host mutations and public activation require their actual scoped authority; generic deployment approval never overrides protection.
- **Estimates:** Supplied 46–74 engineer-days excludes external waiting/ongoing operations. About £0.79/month ex VAT is the dated illustrative incremental OVH cost for 130 GiB objects only; existing dedicated-server bill/capacity, bandwidth, DNS, merchant costs, retention growth and independent drills remain excluded. No permanent staging VM. Qualify real storage usage and tariffs; never prune required evidence to fit the model.

- **Resources:** Proposed aggregate shop CPUQuota=200%, MemoryHigh=6G/MemoryMax=8G, bounded tasks/concurrency at a verified host-controlled shop ancestor including payloads/conmon/network helpers/backups. CPU quota is time, not exclusive cores. Preserve existing cpusets, shared slices/delegation and every guest/service allocation.

- **Storage:** Proposed local ZFS 80 GiB aggregate shop cap including descendants/snapshots, with 50 GiB PostgreSQL data/index/WAL allowance. Account for rootless GraphRoot/images/volumes/temp/logs/certificates/spool; preserve shared journal, reserves, snapshots and disks. `gra` public/private objects; independent off-host `sbg` backups/evidence/artifacts with scoped credentials.

- **Protection:** Inventory every pre-existing rootful/rootless/native/VM resource in all states read-only before the first mx1 deployment write. Unknown ownership is protected. Require docs/host-protection-inventory.md, docs/shop-resource-allowlist.md, separate database identity and complete NixOS activation-impact review before mutations. No protected reload/restart/edit/prune/GC/upgrade/reboot or blanket NixOS activation; rollback is shop-only and preserves business records.

## Key Decisions

| Decision | Rationale | Outcome |
|---|---|---|
| Replace active architecture and deployment planning from the October 21 pair | Explicit user request; new product authority supersedes old inputs | Completed documentation reset |
| Preserve new T01–T14 as the phase/dependency structure | Direct acceptance/evidence traceability to the supplied implementation plan | Current source structure; only explicitly reconciled evidence retained |
| Keep support separate from IP rights and quantities | Non-expiring support purchases and fixed-term IP have different effects | Required source contract |
| Keep P-10 hosting resolved and its qualification pending; other approvals require evidence | Source proposals cannot approve themselves | Affected live operations gated |
| Complete unaffected preparation while external inputs wait | Bank/host/ingress/policy gaps have specific scopes | Required workflow policy |

## Evolution

At phase transitions update validated/active scope and decisions from actual evidence. At milestones review core value, business context and exclusions. Preserve historical acceptance, source revisions and approval records; revise future offers explicitly.

---
*Last updated:2026-10-26, final purchase-flow revision2.*

## Resource credentials — user instruction, 2026-10-21

The agent has access to resource credentials through the repository .env file. When authorized project work needs a credential, consult that file without printing values or copying them into planning, logs, commands, evidence or public artifacts. If the required credential is absent or empty, add a clearly named empty VARIABLE_NAME= entry with a short purpose comment to .env, preserving every existing entry, then ask the user to fill its value directly in that file. Never ask the user to paste secrets into chat. Continue independent work while waiting; do not invent values or approvals. No currently needed missing credential has been identified by this instruction alone.

This operator credential source does not require application .env auto-loading or relax runtime _FILE secrets, fake-only synthetic tests, build exclusions or existing action authorization. Read only the needed credential for the authorized operation; use non-logging process/environment or secret-file interfaces. Resource access is not automatic permission to purchase/provision, modify protected services or perform disruptive tests on mx1/its guests. The independent runner remains unassigned until the user supplies/authorizes it.

## Session context checkpoint — user instruction, 2026-10-21

During project implementation, when session context usage exceeds 90%, run `$gsd-pause-work` at a safe checkpoint before continuing implementation. Save the current position, completed and remaining tasks, evidence, blockers and exact next action in the GSD handoff. Inform the user: “Context usage exceeded 90%. Work is saved. Clear the session, then run `$gsd-resume-work`.” Wait for the cleared/resumed session before further implementation; this instruction authorizes the conditional pause without another confirmation.

Use the context usage indicator supplied by the session when available. If an exact percentage is unavailable, do not invent a measurement or claim automatic threshold monitoring; preserve a handoff proactively when context pressure is apparent and state that limitation. Keep secrets out of the handoff and retain all pending qualification checks as pending.

Active execution policy: [2026-10-22 amendment](EXECUTION-AMENDMENT-2026-10-22.md).

User continuation policy2026-10-23: continue across commits/syncs without ending the turn; stop only when context needs clearing or the user requests it. Context percentage is not available; preserve a handoff proactively when pressure is apparent and state that limitation.


Current requirement delta and routing: [PURCHASE-FLOW-AMENDMENT.md](PURCHASE-FLOW-AMENDMENT.md), STATE.md and ROADMAP.md. Historical continuation/status narratives are retained in the dated pre-amendment archive, not active instructions.

## Local10-04 document reservations — 2026-10-26

Synthetic invoice/credit reservations and separate simulated issue records now archive/read back before commit, retain exact retries and immutable history, and serialize empty/existing series on PostgreSQL. Full recovery of lost terminal history and actual numbering/publication remain gated. [Exact evidence](phases/10-staged-delivery-and-support-ledger/10-DOCUMENT-NUMBERS-PARTIAL.md). Durable statement mail integration is now implemented locally; see the latest statement-capture evidence below. Counts1/14 phases and11/34 plan records; full Phase10 acceptance remains0/6.

Latest10-04 verification: `CORE_LOCAL_PASS checks=5 tests=431 duration_seconds=119.017`; migration0020/no drift and source229 exact files/30 templates/1 CSS/no symlinks pass. Actual off-host recovery remains pending.

## Local10-04 statement capture — 2026-10-26

Archived immutable statement intents now feed the existing leased worker and a durable local capture sink. New-process response-loss retry recovers the same receipt without a new support debit. Current staff generation/assignment and verified owner are rechecked; private status never claims actual email sent. Final focused17 tests and complete-cart demo pass. [Exact evidence and pending gates](phases/10-staged-delivery-and-support-ledger/10-STATEMENT-MAIL-PARTIAL.md). Counts remain1/14 phases and11/34 plans; Phase10 full acceptance0/6.

Retained10-04 verification: full backend448 tests/5 checks,127.821s across two bounded120-second batches; final focused17 tests,7.030s; migration0021/no drift; source232 exact files/30 templates/1 CSS/no symlinks. Supported complete-cart staff/customer response-loss demo passes.

Existing worker regression/mutation lane: `WORKER_LOCAL_PASS checks=6 tests=24 duration_seconds=14.789`. Both required broken-ownership mutations are rejected; forced process interruption/off-host worker qualification remains pending.

Final proxy evidence: `DEMO_ACCESS_PASS checks=102 aliases=2 evidence=local-synthetic-header-level`; owned loopback proxy/Gunicorn/PostgreSQL and current complete-cart fixture, not an independently observed browser engine or formal visual/accessibility approval.

## Local10-05 support refund review — 2026-10-26

Archived owner requests retain available/reserved/consumed support snapshots; distinct recent-MFA per-case staff reviews compare both case and current ledger revisions, append corrections and become outdated after later support activity. All actual refund-policy/amount/eligibility/bank/document approvals remain null. No balance hold, erased work, credit reversal or bank refund. Final focused16 tests pass; [exact evidence](phases/10-staged-delivery-and-support-ledger/10-SUPPORT-REFUNDS-PARTIAL.md). Counts1/14 phases,11/34 plan records and Phase10 full acceptance0/6.

Latest10-05 verification: full backend464 tests/5 checks,141.290s across two finite120-second batches; focused16 tests,6.498s; migration0022/no drift and237-file source/31 templates/1 CSS/no symlinks pass. Actual off-host/core recovery remains pending.

Supported complete-cart staff/customer refund review demo passes: exact request/review retries, distinct assignment and immutable correction; existing ledger revision5/spent1800/available70200 and original bank/entitlement count unchanged. No actual refund.

Final proxy `DEMO_ACCESS_PASS checks=118 aliases=2 evidence=local-synthetic-header-level`: owned loopback proxy/Gunicorn/PostgreSQL. Eight added checks per alias cover refund form/policy, capture redirect, retry identity, consumed-credit detail, owner list, null-origin and missing-CSRF denial, and unchanged ledger balances. Header-level simulation is not independently observed browser-engine or formal visual/accessibility acceptance.

## Local10-06 delivery holds and Phase10 audit — 2026-10-26

The [FUL-01–06 acceptance audit](phases/10-staged-delivery-and-support-ledger/10-ACCEPTANCE-GAPS.md) records implemented local evidence and actual pending inputs. Archived per-entitlement hold/clear controls now gate material/stage publication and private access; cleared holds never resurrect older download grants. Rights/support/money and retained material history remain unchanged. Final focused12 tests and240-file inert source pass; [exact evidence](phases/10-staged-delivery-and-support-ledger/10-DELIVERY-HOLDS-PARTIAL.md). Full acceptance remains pending; counts1/14 phases,11/34 plan records and Phase10 full acceptance0/6.

Latest10-06 full backend476 tests/5 checks,140.823s; focused12 tests,4.648s; migration0023/no drift; source240 exact files/31 templates/1 CSS/no symlinks pass. Application/provider/request/database timeouts unchanged.

Extended `PURCHASE_FLOW_DEMO_PASS` covers actual local staff password/second factor and exact delivery assignment, hold/retry, owner-held status, denied new/old grants, clear, stale-token rejection and fresh post-clear download. Prior three retained material revisions, one intended entitlement/bank operation and support ledger revision5/spent1800/available70200 remain unchanged. No actual delivery/physical recall/rights change.

Final proxy `DEMO_ACCESS_PASS checks=132 aliases=2 evidence=local-synthetic-header-level`: owned loopback proxy/Gunicorn/PostgreSQL; seven additional hold checks per alias cover pre-hold grant, retained held listing/no download forms, new/old grant denial, clear/stale-token denial and fresh access. Control transitions in this HTTP harness use a trusted disposable staff fixture; actual two-factor staff control routes are exercised by the supported complete-cart demo. No real browser-engine/visual/accessibility or actual delivery qualification inferred.

Final full backend `CORE_LOCAL_PASS checks=5 tests=492 duration_seconds=143.124`; both finite120-second batches pass, including16 notification tests, fresh clock/inspection consistency and prior attempt/fulfilment/support/material/number/mail/refund/control suites. Payments0006 applies with no drift. Actual off-host core recovery remains unexecuted.

## Local08-01 notification inbox — 2026-10-26

Archived known-dispatched-attempt hints now feed bounded leases in the existing single worker. Typed fake-bank lookup runs outside DB locks; normalized result/archive readback precedes atomic observation/result/acknowledgement. Hints cannot provide payment fields, start a payment, infer approval or grant fulfilment. Actual callbacks remain disabled. [Exact evidence](phases/08-payment-domain-and-fault-injectable-fake-bank/08-NOTIFICATION-INBOX-PARTIAL.md). Next: scoped overpayment attribution/review. Phase10 local slices retained/full acceptance0/6. Counts1/14 phases and11/34 plan records.

Final existing worker regression/mutation lane: `WORKER_LOCAL_PASS checks=6 tests=24 duration_seconds=15.547`; probe ownership/claim-before-adapter behavior and both required broken-control mutations pass/reject as expected. Forced process interruption/off-host worker qualification remains pending.

Final `DEMO_ACCESS_PASS checks=132 aliases=2 evidence=local-synthetic-header-level` and supported complete-cart demo pass on current code. Demo deliberately loses the fake bank response after commit, enqueues/retries one hint through the local operator, verifies pending state/no inferred payment, and recovers via the existing worker with a failing guard against any second start. Original single bank operation/order/entitlement and72000 support seconds remain once; later ledger remains revision5/spent1800/available70200. Proxy fixture reruns that current demo before both owned loopback aliases. Header-level evidence is not an actual browser-engine/financial/provider qualification.

## Local08-01 overpayment review — 2026-10-26

Explicit exact-pair operator assignments and recent staff MFA now protect archived typed dual-capture evidence, immutable revision/CAS reviews and assigned private staff pages/history. Actual attribution and all refund policies/approvals remain null. Matching amounts do not establish ownership; no new customer payment retry, refund, additional fulfilment or support mutation. [Exact scope/evidence](phases/08-payment-domain-and-fault-injectable-fake-bank/08-OVERPAYMENT-REVIEW-PARTIAL.md).

Final local evidence: backend509 tests/5 checks,150.356s; focused17,6.346s; worker24/6 checks,16.173s (one initial unqualified baseline subprocess failure, unchanged-code rerun passes); supported two-factor complete-cart demo and proxy132 header-level checks/2 aliases pass. Final inert source `/nix/store/58w1hg7cskgjw2w72fwrn0jpi0h3mwi4-shop-python-source`:249 exact files/32 templates/1 CSS/no symlinks. Original intended entitlement/support grant remains once, ledger revision5/spent1800/available70200. Actual callback/financial/provider/runtime/host/off-host recovery/full acceptance remains pending. Counts1/14 phases,11/34 completed plan records; Phase8 full acceptance0/1, Phase10 full acceptance0/6. Next audit remaining Phase8 gaps and select independent authorized local work.

Latest Phase8 routing: [acceptance-gap audit](phases/08-payment-domain-and-fault-injectable-fake-bank/08-ACCEPTANCE-GAPS.md) selects08-02 archived normalized observation journal.08-01 local tasks1–4 are implemented/verified/audited; actual acceptance remains pending. Project1/14 completed phases and11/35 completed plan records; Phase8 full acceptance0/2 and Phase10 full acceptance0/6. Denominator change is a new planned record, not engineering effort.

Latest08-02 local evidence: [archived observation journal](phases/08-payment-domain-and-fault-injectable-fake-bank/08-OBSERVATION-JOURNAL-PARTIAL.md): backend525/5 checks153.829s, combined focused58 including16 journal tests8.902s, worker24/6 checks12.033s, proxy132 header-level checks/2 aliases and final purchase fixture pass. Source253 exact files/32 templates/1 CSS/no symlinks. Local tasks1–4 implemented/verified/audited; actual/full acceptance remains pending. Next plan bounded synthetic authorization/capture intents/history. Counts1/14 phases,11/35 completed plan records; Phase8 full acceptance0/2 and Phase10 full acceptance0/6. Counts are not engineering effort.

##08-03 final local verification —2026-10-27

Backend559 tests/5 checks167.965s (enclosing169.214s), worker24/6 checks13.374s, supported complete-cart two-factor demo and proxy132 header-level checks/2 aliases pass. Exact inert source260 files/33 templates/1 CSS/no symlinks. [Scope and remaining gates](phases/08-payment-domain-and-fault-injectable-fake-bank/08-03-VERIFICATION-PARTIAL.md). Local tasks1–4 complete; actual/full acceptance and hosted CI remain pending. Counts1/14 phases and11/36 completed plan records are not engineering effort.

##13-01 staff finance integration —2026-10-27

Backend560/5 checks168.659s (enclosing169.928s), focused89/19.033s, supported two-factor demo/proxy132/2 aliases and exact261-file source pass. Capture response-loss recovery uses lookup only; full synthetic refund preserves36000 granted seconds and60 reserved seconds. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-STAFF-FINANCE-PARTIAL.md). Actual/full qualification remains pending; continuing local eight-case acceptance.

##13-01 eight-case report —2026-10-27

Supported demo and proxy132/2 aliases pass; four evidence-contract tests reject missing/duplicate/promoted cases. Source checks1–7 pass synthetically;8 remains partial for confidential customer technical intake/custody. Exact261-file source matches. Prepared CI now runs the supported demo; hosted execution remains unverified. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-EIGHT-CASES-PARTIAL.md).

##13-01 optional private follow-up —2026-10-27

Backend569/5 checks171.634s (enclosing172.938s), focused42/16.068s, supported two-factor demo, proxy148/2 aliases and exact264-file source pass. Optional fixed synthetic context revisions preserve accepted scope and ledger, with archive/readback before immutable records and exact owner/recent-MFA staff access. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PRIVATE-FOLLOWUP-PARTIAL.md). Actual technical intake and full qualification remain pending.

##13-01 customer browser engine —2026-10-27

Pinned Chromium155.0.8059.84/test-client Node24.21.0 browser32 checks/2 modes pass; explicit page-script probe proves JS on/off. Four report rejection tests and pinned Node request-policy controls pass. Test tooling only; app source remains exact264-file artifact and frontend Node24.22 native build remains unqualified. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-BROWSER-PARTIAL.md).

Latest browser evidence: [48 checks/2 roles/2 modes](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-STAFF-BROWSER-PARTIAL.md), pinned Chromium155/Node24.21. Both local staff factors, exact assigned/unassigned access and logout are exercised. Actual qualification remains pending.

##13-01 live staff browser revocation —2026-10-27

Pinned browser54 checks/2 roles/2 JS modes passes: retained-cookie scope revoke404, explicit regrant200 and credential revoke403; ordinary logout remains covered. Private inherited controller socket allows six exact ordered fixture operations only, never exposes DB credentials to Node and never retries an uncertain effect. Seven Python report/controller tests and pinned Node origin-policy test pass. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-REVOCATION-BROWSER-PARTIAL.md). Actual/full qualification remains pending; no backend/application bytes changed.

##13-01 public browser preparation —2026-10-27

Required-platform validation now covers current React/Django IP entry; no-JavaScript pages hide inactive React controls. Focused20 backend tests,13 browser-contract tests, default browser54 and proxy148/2 aliases pass. Public20/7 browser and112 frontend tests are explicitly diagnostic only; exact frontend graph/full regression/formal accessibility remain pending. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md).

Final13-01 verification: full backend570 tests/5 checks169.832s (enclosing171.128s), qualified browser58/2 roles/2 modes, proxy148/2 aliases,13 Python browser-contract tests and exact264-file backend source pass. Public20/7 is diagnostic only. Exact Node24.22 native build reached900-second bound/exit124; no build remains. No shared pruning, timeout increase or pin substitution. [Current evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md).

##13-01 exact public qualification —2026-10-27

Retained backend570/5 checks and proxy148/2 aliases; newly qualified exact frontend Node24.22.0/npm11.19.1 with browser58 customer/staff plus public20 JavaScript/7 no-JavaScript checks. Formal/manual and actual/full acceptance remain pending. [Current evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md). Native build/check completed with unchanged pins; separate preparation used two jobs/5400-second bound after observed four-job memory pressure. Acceptance-test limits are unchanged. No actual/full acceptance, phase completion or new commercial/external authority is inferred.

##13-01 keyboard and narrow-screen follow-up —2026-10-27

Expanded exact public browser58 customer/staff plus25 JavaScript/14 no-JavaScript checks pass, including real keyboard/focus, vendor accessibility-tree naming and320px reflow. The observed Django fallback overflow is fixed with the existing shared stylesheet. Focused20 form/cart tests and13 browser-contract tests pass; current inert source264 files/33 templates/1 CSS/no symlinks. Prior backend570 and proxy148 are retained pre-layout-change evidence. [Current evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md). Formal/manual and actual/full acceptance remain pending.

##13-01 business validation accessibility —2026-10-27

Business form now permits only existing same-origin CSS, exposes a validation alert and links errors to invalid fields with safe descriptions. Exact browser98 plus public25/14 pass;10 real-PostgreSQL business privacy/version/concurrency tests(1.424s),13 browser contracts and264-file/33-template inert source pass. Rejected synthetic email is absent, original revision/source retained and invalid submission saves nothing. Prior broad backend570/proxy148 and focused23 staff tests retain earlier scope. Formal/manual and actual/full acceptance remain pending. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md).

##13-01 checkout keyboard review regression —2026-10-27

Exact browser108 plus public25 JavaScript/14 no-JavaScript checks pass, including320px checkout preview, visible keyboard focus, native Enter stale-review409/AX alert and unchanged preview recovery in both modes. Checkout behavior remains unchanged: existing form middleware already permits same-origin CSS. Focused15 real-PostgreSQL checkout tests(2.180s),13 browser contracts and exact264-file/33-template source pass. Prior backend570/proxy148 and other focused tests retain earlier scope. Formal/manual and actual/full acceptance remain pending. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md).

##13-01 payment HTML recovery guidance —2026-10-27

Payment HTML now uses fixed actionable recovery messages while API codes/statuses and service decisions remain unchanged. Exact browser118 plus public25 JavaScript/14 no-JavaScript checks pass, including paid-state disclaimer,320px layout, query-error AX alert, visible Tab focus and Enter retained-status recovery in both modes. Focused17 real-PostgreSQL payment tests(3.619s),13 browser contracts and exact264-file/33-template source pass. Real local response-loss reconciliation retains one attempt/operation and blocks blind resend. Formal/manual and actual/full acceptance remain pending. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md).

##13-01 support error recovery —2026-10-27

Support HTML now uses fixed recovery guidance and an explicit query-free authorized-route link. Exact browser134 plus public25 JavaScript/14 no-JavaScript checks pass, including customer/staff AX alerts,320px visible Tab focus and Enter recovery to unchanged ledger revisions/balances in both modes. Focused24 real-PostgreSQL support ledger/context tests(8.253s),13 browser contracts and exact264-file/33-template source pass. JSON codes/statuses, recent MFA/exact scope, reservation/concurrency/archive controls remain unchanged. Formal/manual and actual/full acceptance remain pending. [Evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md).

Public logout continuation: shared customer denials now include no-store without changing status/body or authorization. Browser134+public43/14 and32 focused PostgreSQL tests pass; [exact evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md). Prior backend578/proxy148 precede this header-only change. No full acceptance inferred.

Detected401 continuation: cart/quotation requests notify customer access, clear private/configuration/pending state and obtain an anonymous CSRF token for verification. Exact fresh browser134+public47/14 and13 contracts pass; [evidence](phases/13-purchase-flow-fulfilment-and-release-acceptance/13-PUBLIC-BROWSER-PARTIAL.md). Backend bytes unchanged from the preceding logout-header fix; actual/formal acceptance pending.
