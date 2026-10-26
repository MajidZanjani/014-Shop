# 014-Shop — Final Purchase-Flow Amendment

**Date:** 26 October 2026  
**Revision:** 2 — final review for a simple purchase experience  
**Repository:** https://github.com/MajidZanjani/014-Shop  
**Domain:** shop.xspi.pro  
**Instruction:** Update the active plan and continue implementation. This revision replaces the earlier 26 October board/support amendment wherever their requirements differ.

## 1. Final decision and instruction to Codex

Keep checkout short. Collect only information needed to determine the licence, approved price, compulsory-support requirement, customer/billing identity and truthful delivery commitment. Obtain detailed engineering information later when the corresponding work needs it.

The principal new customer input is **one board/platform question**, with a conditional kit selection or short description. Do not turn engineering administration into a purchase questionnaire.

Inspect the current authorized repository checkout, preserve completed work, apply this amendment once through the existing project workflow, and continue the next usable local feature. Do not stop after updating planning files.

Confirmed business requirements remain:

- Support concerns SLL's own IP and the board/FPGA/memory guidance needed to integrate it. This does not create unrelated third-party-IP support or general consultancy products.
- A customer can buy an approved SLL R&D licence with support while the board is being designed.
- Approved initial R&D RTL/key/documentation may be delivered before the customer-specific reference design is ready. Keep the later reference design as an explicit outstanding obligation.
- Suitable approved kits may be purchased without additional support. Other approved offers may require support. SLL defines those rules; customers do not classify their own requirement.

**An unlisted, custom or unfinished board does not automatically require manual review before payment.** If an approved standard R&D-plus-support offer covers the selected licence and development engagement, let the customer purchase it with basic platform information. Review before payment only when a missing fact prevents establishing the approved price, licence rights, compulsory support or honest delivery scope.

Approval of a standard catalog offer can be established in advance. Do not add individual engineering approval to every normal purchase.

## 2. Final review of the previously added/updated requirements

“Required at purchase” below means information or behavior necessary for the sale; it does not mean every item becomes a customer-entered field.

| Previous item | Final decision | Implementation treatment |
|---|---|---|
| Ask which development kit or board is used | **Keep at purchase** | One platform question and only the relevant conditional kit/name detail. |
| Ask for a separate detailed project stage | **Remove as a compulsory purchase field** | The “board not designed / need guidance” platform answer captures the essential distinction. Ask further stages during support only if useful. |
| Collect pinouts, schematics and constraints | **Move to engineering follow-up** | Request privately when needed to prepare the reference design; not a normal checkout requirement. |
| Collect full FPGA part/package, memory details, tool versions and performance goals | **Move to engineering follow-up by default** | Ask a narrow detail before payment only if it changes the actual offer or immediate ready-design promise. Preserve the existing licensed vendor/family selections. |
| Recognize kits with an available reference design | **Keep as internal catalog data** | Maintain a small approved kit/offer mapping. Do not build an exhaustive hardware database. |
| Allow appropriate kit purchases without support | **Keep and enforce at purchase** | Show support as optional where the approved offer allows zero additional support. |
| Require support for designated cases | **Keep and enforce at purchase** | Derive the requirement and approved minimum from the offer. Display its scope and price; prevent its removal through request tampering. |
| Explain support requirements across FPGA offerings | **Keep as concise product/summary copy** | No additional customer questionnaire or separate recommended-support workflow is required. |
| Sell R&D plus support during board development | **Keep as an approved standard purchase path** | Final pinouts, a finished board and a completed reference design are not prerequisites for that development offer. |
| Deliver R&D materials before the custom reference design | **Keep as fulfilment behavior** | Show the later obligation clearly. Use existing order/deliverable statuses rather than a project-management system. |
| Specify the reference design and engineering scope | **Keep a concise offer description** | Use approved standard terms for ordinary sales. Review genuinely nonstandard promises separately. Do not make customers enter artifact/version identifiers. |
| Limit support to SLL IP | **Keep as scope and automatic order association** | Infer the SLL product from the order/support account; no extra “prove your IP” form for a combined new licence/support purchase. |
| Track target, policy and document revisions | **Keep necessary internal records** | Snapshot the selected offer/platform automatically. Record engineering document versions later when received. |
| Add a dedicated engineering-case/upload portal | **Remove as a required feature of this amendment** | Use existing order/support records and an already authorized confidential follow-up channel. A new portal is optional later work. |
| Automate cross-project support-credit pooling | **Remove as a new implementation prerequisite** | Retain existing ledger behavior. Use staff-assisted, recorded allocation for eligible-credit exceptions where needed. |

These decisions preserve the manager's requirements while reducing what the customer must do before paying.

## 3. Minimum customer purchase flow

### A. Configure the licence and identify the platform

Retain existing applicable licence selections: vendor, licensed families, term, production band where relevant, and access mode/node/seat quantities where relevant. Preserve the existing approved licence-host requirements; do not duplicate them in board intake or confuse a workstation host ID with an FPGA board.

Add this question:

**Which board or development kit will you use?**

1. **A listed development kit** — select its approved catalog entry.
2. **Another kit or a custom/modified board** — provide a short name/model if known; allow “not yet named/unknown.”
3. **Board not designed or selected / I need board-design guidance.**

For a listed kit, include the relevant standard revision/configuration in the choice. Ask a further variant question only when it changes the offer, compulsory support or applicability of the ready reference design. Do not ask customers to re-enter hardware details already established by that catalog choice.

For other boards, a detailed project name, revision history, full device specification, pinout and performance target are not universal purchase requirements. Basic platform answers can select an approved development offer.

An unknown board is valid for an applicable development offer; an unknown licence scope is not. The purchaser must still select the vendor/families and rights actually being bought.

### B. Show the offer and applicable support

Automatically display:

- The SLL IP licence and its licensed scope.
- The included reference-design description: an available kit design or an agreed later design.
- Whether additional support is optional or required.
- The approved support package quantity/minimum and price where required, with a short explanation.
- The total, applicable licence period/start rule, terms and delivery conditions.

These are seller-controlled offer data and calculated outputs. Do not ask the customer to enter a support-policy category, approval ID, reference-design revision or engineering reviewer.

Use two normal support messages: **optional** or **required**. Recommendations can be ordinary optional explanatory text. Missing commercial policy uses the existing quotation/review outcome; it does not require another workflow platform.

Required support must be visible in the price and applicable terms, not silently added at the final payment step. Do not assume that every custom board requires one ten-hour package or that ten hours guarantees a completed custom design.

### C. Complete the existing business checkout and pay

Retain the approved customer/licensed-entity, billing/tax, end-use, acceptance and payment requirements. This amendment does not waive required commercial information.

Use the existing simplifications: billing address can match the registered address, the technical contact can match the purchaser, the licensed entity can default to the purchasing entity, and invoice email can default to the purchasing email. Keep existing optional fields optional and country-dependent fields conditional.

Do not add project registration, technical uploads, an engineering interview or staff sign-off to every standard checkout. Reuse the existing applicable acceptance controls rather than creating a new checkbox for each internal engineering step.

## 4. When review before purchase is genuinely needed

Use an already approved standard offer whenever it honestly covers the sale. Custom or unfinished hardware alone is not a reason to interrupt that path.

A narrow clarification or reviewed quote is necessary when, for example:

- The actual price, licence rights, compulsory support or included delivery scope cannot be established from an approved offer.
- A kit variant or hardware modification makes the promised ready reference design uncertain, and no suitable approved development offer covers the request.
- The customer requests a bespoke fixed-price/result commitment beyond the standard package.

Ask only what resolves that exception. Do not automatically request a complete engineering dossier.

Known excluded targets and requests solely for another supplier's IP remain unavailable under this scope. Buying support does not make them eligible. Preserve all other existing mandatory commercial holds.

Do not silently change a ready-design purchase into an unspecified development engagement. Present the appropriate approved offer and let the customer accept its actual scope. Preserve the existing rule against charging an unapproved basket or silently dropping/splitting its lines.

## 5. Engineering and fulfilment after purchase

The purchase creates the order and support association automatically. An additional customer-created project record is unnecessary for a normal sale.

During the subsequent work, SLL can request the pinouts, schematics, FPGA/memory details, tool versions or goals needed for that task. Use existing authorized private communication/file exchange where available; no new upload portal is a prerequisite for this checkout change. If a secure submission capability is genuinely missing, address that capability before accepting technical files rather than using a public form or bucket.

Keep confidential customer files out of Git, public static output, URLs and ordinary logs. Never execute uploaded EDA scripts as part of this intake. Apply existing customer/staff permissions to any stored material.

Use existing fulfilment records for the staged R&D path:

1. Accept and fund the approved R&D/support order; grant purchased support credit once.
2. Release the available approved R&D materials when their payment, licensing and delivery prerequisites are satisfied.
3. Obtain technical information and perform the agreed support work.
4. Prepare/review and deliver the promised reference design, closing that outstanding obligation.

Initial delivery must not mark the later reference design complete. Later reference-design delivery must not create another paid IP entitlement. Preserve the promised reference design; do not simplify the product into a support-time-only service or silently remove an included deliverable.

Record the actual technical documents/design versions used as internal fulfilment evidence. Customers need not enter those identifiers. Handle subsequent scope changes through the existing order/support process, preserving accepted history and unrelated licence rights.

### Support balances

Keep the existing ten-hour, non-expiring package and actual-work ledger rules. Support does not grant or extend IP rights. Preserve later SLL support top-ups without requiring a new IP licence or another board questionnaire.

If a customer requests use of existing credit, apply an approved ownership/scope policy using existing functionality or staff-assisted confirmation and recorded reservation. Prevent double allocation. Do not force a duplicate purchase where eligible credit is already approved, or invent cross-project sharing rights. A credit exception may need review of that order; automated pooling is not a prerequisite for ordinary checkout.

## 6. Seller setup that still matters

These are SLL configuration decisions, not extra customer form fields:

| Seller input | Minimum required decision |
|---|---|
| Ready kit offers | Initial supported kit variants, matching design description and applicable support policy. |
| Standard development offers | Approved SLL R&D scope, support requirement/minimum, price and honest later-delivery commitment. |
| R&D period | Approved annual start trigger and rights. Reuse an applicable existing decision; do not invent one. |
| Design/work scope | What is included, what consumes support credit, and when additional work needs authorization. |
| Existing-credit exceptions | Eligible owner/scope and the process for confirming/reserving credit when requested. |

Reuse the existing decision register and approved values. Unknown commercial values keep only the affected live offer pending; they do not block local implementation or unrelated approved sales. Use explicitly synthetic fixtures for development.

Do not require approval of every possible board before launch. A short ready-kit list, approved standard development offers and a scoped exception path are sufficient.

## 7. Bounded Codex implementation

1. **Inspect and reconcile.** Read the current checkout and relevant source precedence. Preserve completed work. The review baseline was the 21 October documents at commit 84343d56378f0cf69eabd350734eb32052e9a37c; no assertion is made that the latest remote is unchanged.
2. **Update active requirements once.** Register this final revision as the current amendment. Preserve historical product snapshots/hashes, and make precedence explicit. Remove superseded mandatory checkout questionnaires, blanket custom-board review and portal prerequisites from active plans/tests.
3. **Implement the minimal flow.** Add the platform choice, conditional kit/name detail, approved offer/support selection and concise delivery summary to the existing catalog/configurator/backend/no-JavaScript path.
4. **Keep records small.** Save the selected platform and accepted offer/support/delivery snapshot in existing order/configuration records. Extend existing support/fulfilment statuses only where needed; avoid a separate project-management system.
5. **Continue to a usable result.** Complete the ordinary purchase path with the existing payment implementation or clearly synthetic adapter. Implement staged delivery in its actual dependency order. Do not stop after the plan edit or reopen unrelated infrastructure work.

Affected areas are T01/T03/T04/T07/T10/T13, with narrow T05/T06 record/access changes only where needed. A new engineering-case portal, comprehensive technical-intake UI, new general workflow engine and automated credit-pooling system are not required by this amendment. Preserve existing useful functionality rather than deleting working code merely to simplify the plan.

Retain shop.xspi.pro, the existing Astro/React and Django/PostgreSQL architecture, and all protected-server rules. No protected service edits/reloads/restarts, blanket NixOS activation, infrastructure purchase or new live bank/mail/DNS/deployment authority is granted. Stalwart, Webadminproxy, Plesk, existing PostgreSQL, Prometheus, Grafana/grafana-tls, Blackbox, Alertmanager, MicroVMs, NetBird, Matrix and all other pre-existing or uncertain resources remain protected. Keep disruptive qualification off-host and external gates separate from ordinary local development. Continue excluding the superseded Free Trial IP Form.

Use focused tests and concise progress records. Preserve the user's context-checkpoint instruction. Do not turn this simplification into another large planning phase.

## 8. Acceptance checks and handover

Verify these changed behaviors:

1. An approved ready kit permits zero additional support when its policy allows.
2. An approved R&D-plus-support offer can be purchased with “board not designed” and no uploaded pinout.
3. An unlisted/custom board does not automatically force manual review when an approved development offer applies.
4. The required support cannot be removed by browser/API tampering; the no-JavaScript flow uses the same rules.
5. Undefined price/rights/delivery terms and a known unsupported ready-design promise still prevent the affected sale.
6. Initial approved R&D delivery leaves the later reference design outstanding; later delivery does not duplicate entitlements.
7. Existing SLL support top-ups require no new licence or board questionnaire; confirmed credit is not double-allocated.
8. Technical information collected later stays private, and accepted order scope/history remains intact.

Report the updated plan clauses, the local purchase path that now works, a reproducible demo/build command, focused checks actually run, and remaining specific live-operation dependencies. Clearly distinguish implemented behavior, synthetic evidence and pending qualification.

## Source basis

This final revision applies the manager's board/reference-design requirements, the user's SLL-only support and staged-R&D confirmations, and the user's subsequent instruction to keep the purchase simple.

Baseline references for retained product requirements:

- [Proposal — configuration, checkout, support and delivery](https://github.com/MajidZanjani/014-Shop/blob/84343d56378f0cf69eabd350734eb32052e9a37c/SLL-xSPI-MC-Shop-Proposal-2026-10-21.md).
- [Handoff — product invariants and T03/T04/T07/T10](https://github.com/MajidZanjani/014-Shop/blob/84343d56378f0cf69eabd350734eb32052e9a37c/SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md).
- [Original product definition — licensing, deliverables and business checkout](https://github.com/MajidZanjani/014-Shop/blob/84343d56378f0cf69eabd350734eb32052e9a37c/docs/product-source/SLL_xSPI_MC_Product_Page.md).

Keep the old sources as historical evidence and use this revision for the specific changed requirements. Do not infer that all original plan items have been implemented or externally qualified.
