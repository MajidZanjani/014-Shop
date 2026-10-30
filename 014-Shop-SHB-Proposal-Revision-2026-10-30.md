# 014-Shop — Supporting Hours Bundle proposal revision

**Date:** 30 October 2026, Asia/Tbilisi  
**Revision:** 1.1 — manual support-time tracking  
**Project:** Synaptic-Online-Shop / 014-Shop  
**Repository:** https://github.com/MajidZanjani/014-Shop  
**Customer origin:** https://shop.xspi.pro  
**Purpose:** Revise the existing plan and continue implementation of an invitation-only shop whose first and only visible product is **Supporting Hours Bundle**.

**Revision 1.1 change:** The shop records each purchased bundle and its hours, but does not calculate used or remaining support time. SLL's support team maintains those records manually and manually emails the customer after each support session/task. No online time ledger, automated hour credit/debit, usage-email automation, or customer balance/bundle panel is required. This change applies throughout the operative proposal, implementation scope and acceptance criteria; it supersedes contrary automation requirements in revision 1.0 and earlier plans. [U2]

## Executive decision

Pause new IP-product sales. Launch one product, **Supporting Hours Bundle**, with exactly these selectable variants:

| Customer-visible option | Hours per bundle | Commercial treatment | Initial action |
|---|---:|---|---|
| **FPGA Supporting Hours Bundle** | **10** | An approved hourly rate, sold in whole bundles; ordinary eligible purchases are automated | **Checkout** |
| **ASIC Supporting Hours Bundle** | **25** | A higher approved base hourly rate; each requested scope requires SLL technical review before purchase | **Submit Request** |

Use a shared customer form, positive integer quantity, optional discount code and clear price summary. Reuse the existing Astro Content Collections, React islands, Django, shop PostgreSQL, bank adapter, order records and staff administration. The support team handles subsequent time usage, remaining hours and task emails manually outside the shop. Keep the IP product and its records available for future development, but remove it from the active storefront and reject new IP purchases through backend routes.

Implement access using **https://shop.xspi.pro/invite/<random-token>**. Each invitation expires **six calendar months after creation**. A server check, including checks on the static storefront, enforces expiry. Purchased FPGA support hours retain the attachment's **no-expiry** rule. This proposal recommends the same rule for ASIC and identifies it as an addition requiring commercial adoption before paid ASIC offers become live.

The attached document is a draft FPGA product page and support-policy source. It contains a price placeholder and expressly requires final policy links/wording before publication. It does not contain an ASIC agreement or an ASIC purchase form. This revision supplies those implementation requirements without inventing prices, tax treatment, bank capabilities or legal approval.

## 1. Authority, prior decisions and scope change

### 1.1 Sources reviewed

This revision uses the earlier project conversations, the 21 October shop proposal, the final 26 October purchase-flow amendment, the 26 October repository review, the 28 October commercial-binding discussion, the user's product instruction and subsequent manual-support-tracking instruction, and the attached support policy. Source details appear in section 16. The complete attachment is preserved as historical source in Appendix A so this handoff is self-contained.

The repository review described a snapshot at commit `c8302978660912ef6a00effd8a718746e6d624d1`; it is historical evidence, not a statement of the repository's current state or an instruction to reset to that commit. Codex must inspect the current authorized worktree once and preserve subsequent work.

### 1.2 Precedence

1. The user's 30 October directions control the product name, two variants, bundle sizes, purchase/request paths, invitation lifetime and common fields, and require manual support-time tracking and task emails with no online balance panel or available/used-time calculations.
2. This revision resolves the implementation gaps and changes active scope. Explicitly identified commercial recommendations are proposed terms, not evidence that SLL has already approved them.
3. The attached FPGA policy supplies existing FPGA support scope and service terms, subject to its own draft placeholders and publication note.
4. Earlier requirements continue where relevant and consistent. Their security, financial/order accounting, recovery and protected-service controls remain applicable. Earlier automated support-ledger, time-credit/debit, usage-email and balance-display requirements are expressly deferred from this SHB release by the user's later instruction.

Do not amend historical customer contracts, accepted orders, entitlement records or evidence hashes when revising the future storefront.

Preserve any existing time-ledger code and historical data safely, but do not connect new SHB purchases to automated time accounting or make that module, its usage controls, or its dedicated qualification a launch dependency. Document the scope change in existing planning records rather than silently deleting history or weakening shared payment/security checks.

### 1.3 Retained versus deferred requirements

| Area | Revised treatment |
|---|---|
| Astro Content Collections and React islands | Retain. Human-editable Markdown remains the source for approved product and policy copy. |
| Django, independent shop PostgreSQL and durable worker | Retain. Reuse existing components and installed, pinned versions. |
| Rootless Podman on the existing OVH NixOS dedicated server | Retain the selected deployment direction and all existing isolation/qualification requirements. |
| AWS Route 53 and shop.xspi.pro | Retain. No per-customer DNS records are needed for the recommended invitation design. |
| Public Object Storage storefront | Replace public delivery of protected shop content with access-controlled delivery from a private release; section 7 explains the necessary change. |
| Bank-hosted payment, verification, reconciliation and refunds | Retain for FPGA and subsequently approved ASIC offers. |
| Support-time tracking and task-usage emails | Support team handles both manually outside the shop; no automated time accounting or task-email generation. |
| Customer available/used hours or bundle panel | Not required. Do not build a customer dashboard or balance API for this release. |
| Short checkout and later engineering follow-up | Retain. No mandatory pinouts, design uploads, project portal or full engineering questionnaire. |
| New IP sales, licence configurator and IP-specific fulfilment | Defer from the SHB launch. Preserve code, history and obligations already created. |
| Paused IP-sale commercial decisions | No longer blockers for selling support alone. Only relevant existing licence/eligibility facts remain necessary. |
| Superseded Free Trial IP Form / Monday.com intake | Remain excluded. |
| Additional proprietary SaaS or a replacement commerce platform | Not required. |

The earlier board-development discussion allowed SLL-IP integration guidance while a customer designs a board. The attachment excludes PCB design/layout and substantial separate development. Preserve that boundary; SHB does not silently become a general PCB-design or third-party-IP consultancy service. [P1][P2][S1]

## 2. Product model and pricing

### 2.1 One product, two variants

Use a product identifier such as `supporting-hours-bundle` and stable internal variant identifiers such as `shb-fpga-10h` and `shb-asic-25h`. These are implementation suggestions, not required renames of established identifiers.

The visible title must be **Supporting Hours Bundle**. Use the full variant labels above in the selector, review, order confirmation and invoice. The abbreviation SHB may be used internally. Do not create two independent product cards or display the paused IP product as a teaser or disabled purchase tile.

One checkout/request contains one selected variant and one bundle quantity. Retain an existing cart internally if useful, but this release does not need a separate multi-product cart page. Switching the variant updates the hours, rate, applicable fields, discount eligibility and action button.

### 2.2 Authoritative calculations

Let `q` be a positive integer number of bundles, `rF` the approved FPGA hourly rate and `rA` the approved ASIC hourly rate, in the same approved currency:

| Calculation | FPGA | ASIC |
|---|---|---|
| Hours purchased in this order | `10 × q` | `25 × q` |
| Undiscounted bundle price | `10 × rF` | `25 × rA` |
| Undiscounted subtotal | `q × 10 × rF` | `q × 25 × rA` |

Require `rA > rF` for the base rates. Do not invent a multiplier. A discount changes the amount paid, not the hours purchased. A lower discounted effective rate is allowed only through an applicable approved discount policy; do not invent a margin floor.

Store the bundle size, quantity and purchased hours on each immutable order line. This is a record of that purchase, not a live support balance. Do not calculate cumulative purchased, used or remaining hours across orders, issue online time credits, or maintain a seconds-based support ledger for this release.

Use approved decimal-money/currency rounding rules or integer minor units. Never accept browser-supplied rates, total hours, tax, discount amounts or approval flags as authoritative. Validate quantities on the backend, reject zero/negative/fractional/overflow values, and use the bank's qualified transaction limits when deciding payment bounds. Keep all totals consistent between JavaScript, no-JavaScript forms, order snapshots and bank requests. [W3][W5]

EUR is suggested by the attachment's euro placeholder, but the actual supported settlement/presentment currency and numerical rates remain commercial inputs. Never publish `[PRICE]`, silently substitute zero, or promote a development fixture into a live price.

### 2.3 Price display

Show the hourly equivalent, hours per bundle, bundle quantity, total hours, subtotal, discount, tax and final total. The customer buys whole bundles; displaying an hourly equivalent must not suggest that arbitrary single hours can be purchased.

FPGA shows a payable total once billing/tax information is sufficient. ASIC initially shows **Estimated total — subject to technical review and an approved offer**. If an ASIC rate is still unavailable, show **Price to be confirmed** and allow only an otherwise approved request-intake flow; never show an invented estimate. Its final approved offer must disclose the exact payable amount before payment.

## 3. Customer interface and minimum information

### 3.1 Shared form

Retain every field requested by the user:

| Field | Required treatment |
|---|---|
| Company Name | Required legal purchasing-company name. |
| Address | Required billing address and country; use country-appropriate city, region and postal-code requirements. No separate shipping address. |
| Phone | Required; label **Company Phone** for clarity and allow international format. |
| Contact Person (Full Name) | Required. |
| Contact Phone Number | Required; offer **Same as company phone** to avoid repeated typing. |
| Contact Email | Required and validated. Use for this transaction under existing contact controls; an entered address does not automatically replace an authorized company contact or gain access to account history. |
| Bundle quantity | Required positive integer; default 1. |
| Discount code | Optional, with Apply/Remove, result message and recalculated price. |
| VAT/tax identifier | Conditional on the approved tax rules, with **Not applicable** where appropriate. Do not demand a VAT number from every company. |
| Terms acceptance | Unchecked, appropriate to the stage; record exact document versions and timestamp. |

Use the invitation's internal customer and eligibility association; do not trust a submitted customer/account ID. Do not merge legal entities merely because their names or email domains look alike. Handle a different purchasing company through a narrow clarification/new invitation, rather than silently moving another customer's account or purchase records.

The address is a billing/tax input, not an IP-derived location. Do not infer customer geography from IP addresses, VPN endpoints, browser language or email domains.

Reuse approved business/end-use checks when actually needed for this support sale. Prefer known customer/invitation data and conditional exception handling over carrying forward the paused licence product's entire questionnaire. No licence-term selection, board selection, host ID, production-volume band or new-IP entitlement is required to buy SHB.

### 3.2 Additional FPGA input

No engineering problem description is required to buy a normal FPGA top-up. A customer may buy hours before a specific task exists.

Before issuing an invitation that permits automatic FPGA purchase, SLL establishes that the customer has an eligible relationship/licence for the supported SLL IP and relevant supported target. Save that association internally. The invitation can reference an approved list of eligible SLL products without making the customer repeatedly prove their licence or choose a new product licence.

The attachment's supported FPGA families remain an editable, approved compatibility list. Other families require prior agreement. If eligibility is unknown or the customer requests work outside that scope, clarify the exception before taking payment; the normal prequalified path remains automated. [S1: Supported FPGA Families; P2]

### 3.3 Additional ASIC input

The attachment's device/tool/log checklist describes later FPGA support intake, not a mandatory checkout form. For ASIC review, collect only:

| Additional field | Treatment |
|---|---|
| SLL IP/product or existing support/project reference | Required if not already associated with the invitation. Reuse known information. |
| What assistance do you need? | Required short description of the requested work and objective. This is the principal feasibility input. |
| Relevant design stage, technology/process and tools | Optional compact field; ask only pertinent details and permit **Not yet known**. A reviewer requests missing facts if they affect feasibility. |
| Desired timing or deadline | Optional; allow **No fixed deadline**. It is a requested date, not an SLA. |

Do not require RTL, PDKs, tool credentials, logs, waveforms, schematics or other uploads at this stage. Ask for technical materials through the established confidential channel when needed. Never execute submitted design files/scripts as a form-processing operation.

### 3.4 Customer-visible scope statements

Use concise copy near the summary, with details in the policies:

- Support concerns the use and integration of supported **SLL IP**.
- A bundle buys engineering time; it does not buy an IP licence or guarantee a particular result.
- No response-time or resolution-time SLA applies unless separately agreed.
- FPGA support hours do not expire. Apply the same statement to ASIC only after the proposed ASIC terms are adopted.
- Shop invitation expiry does not cancel purchased support or remove unused hours.
- ASIC requests are reviewed before an offer can be purchased.
- SLL's support team keeps the support-time records and emails the customer after each support session/task with time used and the remaining hours. There is no online support-time/bundle panel.

Preserve all remaining scope exclusions, confidentiality, ownership and customer-responsibility provisions described in section 10 and Appendix A.

## 4. FPGA purchase flow

1. The customer enters through a valid invitation and selects **FPGA Supporting Hours Bundle**.
2. The customer chooses quantity, fills the common form and optionally applies a discount.
3. The backend confirms invitation scope, current eligibility, approved rates/tax rules, discount applicability and applicable terms. The review displays the exact purchase.
4. **Checkout** creates or resumes the same immutable order/payment attempt under the existing repeat-safe transaction rules and redirects to the bank-hosted payment page.
5. The bank result is verified through the qualified server-side integration. A browser return page never establishes payment by itself.
6. After both order acceptance and verified successful payment, finalize the paid order **once**, retain its `q × 10` purchased FPGA hours, record coupon use once, and queue the transaction confirmation/invoice or receipt. Make the paid order and its reference reliably available to the support team through the existing staff order view and configured order notifications. Do not create an online hour credit or require a manual balance update before completing normal checkout.
7. The invitation-based confirmation page states only the hours bought in this order and the authorized support contact/channel. The support team manually records the purchase, later tracks time used/remaining and manually sends each support-task email to the authorized contact. No running balance is calculated, displayed or emailed by the shop. A form-entered email does not automatically replace the company's authorized support contact.

Preapproved offers and invitation eligibility make ordinary FPGA orders automatic. Exceptional payment, identity, compliance or tax failures remain specific holds. Do not add technical staff approval to every normal FPGA purchase.

## 5. ASIC request, review and later purchase

### 5.1 Initial request

The customer selects **ASIC Supporting Hours Bundle**, chooses 25-hour bundle quantity, completes the common form and brief ASIC details, and optionally applies a discount. The button reads **Submit Request**, never Checkout at this stage.

Before submission show: **Submitting a request does not charge you or reserve engineering availability. SLL will review the requested support and contact you with an approved offer or questions.**

Store the request before acknowledging it. Return a request reference and send an acknowledgement through the existing mail mechanism. The first feasibility review is proposed as pre-sales administration: no customer hours are debited and no paid investigation starts without an explicit agreement. A technical analysis beyond that review can be separately offered.

### 5.2 Staff review

Reuse the existing staff interface and permissions. The reviewer establishes whether SLL can support the requested SLL-IP work, has the necessary expertise/capacity, and can legally access any required customer materials, EDA environment or process information. There is no assumption that SLL possesses every EDA licence or PDK.

Use a small state model:

| State/outcome | Effect |
|---|---|
| Submitted / Under review | No payable order, no charge and no completed support purchase. |
| More information required | Ask only questions needed for feasibility; preserve the request and any eligible discount reservation. |
| Declined / Withdrawn | Close the request, notify the customer as appropriate, release its unused coupon reservation. |
| Approved | Record the approved scope and prepare a dated commercial offer. Technical approval alone is not a completed purchase. |
| Offer issued | Customer can review and accept the exact approved offer while valid and with authorized shop access. |
| Payment pending / uncertain | Preserve the offer/order and reconcile using the existing bank lifecycle. |
| Paid and accepted | Finalize the paid order once with `q × 25` purchased ASIC hours and the approved scope; confirm the purchase and make the order available to the support team for manual tracking. |
| Offer expired | No new checkout against the expired offer. Reissue through an explicit staff action if appropriate. |

### 5.3 Approved offer

Bind the offer to the customer, request revision, SLL IP/project scope, prerequisites/exclusions, quantity, total hours, rate, discount, taxes, amount, currency, applicable terms and expiry. Recommend an offer validity of **14 calendar days from issue**, visibly stated. This is separate from the six-month invitation and is a proposed operational default.

Use an already approved standard ASIC price/terms revision when applicable. Do not demand a second commercial approval for each routine request if the reviewer stays within those preapproved terms. Custom rates or materially different promises need the appropriate commercial approval.

The customer reviews and accepts the final offer, then proceeds to **Checkout** and the same bank flow. If SLL changes requested quantity, scope, price or timing commitments, disclose the changes and obtain customer acceptance. A material edit to an approved request invalidates the old approval for the changed work; issue a new revision.

The checkout API must refuse ASIC purchase without a matching valid approval and accepted offer, even if the customer changes hidden fields or invokes the API directly. An approved offer cannot be reused for another company/project or finalized repeatedly as duplicate purchases. Preserve payment reconciliation and repeat-safe order processing. [W3][W5]

If shop access expires during review, review may continue. SLL issues a replacement six-month invitation when customer access is needed; issuing a quote must not silently extend the original invitation or turn an unprotected quote URL into a shop-access bypass.

## 6. Six-month invitation design

### 6.1 Recommended URL

Use **https://shop.xspi.pro/invite/<random-token>**. The example is a pattern, not a real credential.

The user's example `<token>-shop.xspi.pro` is technically possible with suitable routing/certificate coverage, but puts the access secret into a hostname and DNS-related handling. A fixed hostname keeps DNS/TLS and bank URLs stable. Route 53 does not support `*-shop.xspi.pro` as a partial-label wildcard; TLS wildcard matching also uses a whole leftmost label. No DNS or certificate mechanism establishes the six-month authorization rule. [W6][W7][W8]

### 6.2 Definition of six months

Use **six calendar months**, not 180 days. Compute the expiry from creation in **Asia/Tbilisi**, preserve local time of day, clamp to the last day when the destination month lacks that day, and store the resulting instant in UTC. Compare against trusted server time. Access is allowed only when `now < expires_at` and the invitation is not revoked.

Examples, all shown in Asia/Tbilisi:

| Created | Expires |
|---|---|
| 30 October 2026, 10:00 | 30 April 2027, 10:00 |
| 31 August 2026, 10:00 | 28 February 2027, 10:00 |
| 31 August 2027, 10:00 | 29 February 2028, 10:00 |

Opening a link, visiting repeatedly, submitting a request or buying a bundle never restarts its lifetime. A replacement invitation is a separate auditable issue/revoke operation, not an invisible extension.

### 6.3 Authorization and privacy requirements

Generate 32 cryptographically random bytes, encode them safely for a URL, and store only a cryptographic digest for lookup plus the invitation's internal ID, customer scope, allowed modes, issuer, creation/expiry and revocation state. Keep raw tokens out of source control, normal database records, logs and analytics. If mail retry temporarily retains a token, treat that payload as a protected secret with short retention.

A valid invitation establishes a shorter framework-managed browser session and redirects to the clean shop URL. Use host-only Secure/HttpOnly cookies and the existing appropriate SameSite/CSRF protections. The session's hard expiry must be no later than the invitation's expiry; check current invitation expiry/revocation on every protected request. Reuse an established shorter session limit; otherwise an eight-hour maximum is a proposed default.

Require HTTPS, redact invitation tokens at every ingress/application/error-log layer, use `Referrer-Policy: no-referrer`, and disable storage of protected responses in browser/shared caches with appropriate `Cache-Control: no-store`. Keep third-party tracking off this flow. Authentication/access denial must fail closed. These are implementation applications of authorization/session guidance. [W1][W2]

The invitation is deliberately **reusable** until expiry. Email scanners and previews may visit it; a GET must never consume it, create a purchase/request, reserve a coupon or send customer messages. State-changing actions require deliberate protected submissions.

### 6.4 What possession of the link proves

A bearer link proves possession of that link. It can be forwarded. Binding a company ID or asking somebody to type a known email address does not prove personal identity. [W9]

For the initial shop, scope the invitation to viewing the offer and starting permitted new purchases/requests. Do not give it access to historical invoices, prefilled private customer details or confidential files. Preserve existing verified-contact/resource-access controls for any retained private resources; this does not require building a new customer portal. No support balance, usage-history or bundle-management panel/API is part of this release. A named-recipient-only experience would additionally need mailbox verification at entry. It is not implicitly guaranteed by the user's link-only requirement.

Use the issued customer/eligibility association on the server. Form edits cannot authorize access to another customer, change the scope of a price agreement, or attach a purchase to a guessed customer record.

### 6.5 Expiry boundaries

On expiry/revocation deny new storefront access, new request submission and new checkout initiation. Show a generic message directing the customer to SLL for a new invitation, without revealing the associated customer.

Expiry does **not** expire hours, reverse payment, cancel existing contracts, delete records or prevent staff completing a submitted ASIC review. Paid support remains usable through SLL's normal support channel.

Bank notifications, refunds and reconciliation use their own authenticated service route and do not require a customer session or current invitation. A payment initiated legitimately before expiry is handled under its recorded payment deadline and actual bank state; delayed notification is not grounds to lose or ignore money. Abnormal genuinely late payments enter reconciliation/refund review according to the approved policy. Do not reopen checkout through the expired invite. [W3][W4]

## 7. Required hosting adjustment

OVH's documented Object Storage static-website mode requires public-read access. An invitation check in front of a publicly readable copy can be bypassed by requesting that copy directly. Authorization must cover protected static content as well as application APIs. [W10][W1]

Keep Astro static generation and the existing React islands. **Change the delivery boundary:** keep shop releases private in Object Storage, and serve the approved built release only through the isolated shop service's authorization gate.

For this small release, prefer deploying the approved private build snapshot into the existing dedicated shop runtime, where Django authorizes protected routes and the isolated gateway/protected file route serves only manifest-approved files. Reuse existing safe implementation primitives; do not add another application platform or runtime merely for this gate. Object Storage remains available for private release artifacts and backups. If the current code already supports a qualified private-object fetch path, reuse it instead of building a second delivery mechanism.

The gate must cover HTML, catalog JSON, prices, offers and protected assets. No public bucket URL, alternate hostname, preview build, old IP route, source map or static data endpoint may expose the protected storefront or an alternate purchase route. Non-sensitive public legal/contact pages and a generic access-required page can remain reachable. The bank webhook is a narrowly authenticated service endpoint, not an anonymous customer bypass.

`robots.txt`, `noindex`, JavaScript redirects and hidden buttons can supplement presentation but do not implement access control. Do not publish a protected offer in public static JSON and rely on frontend code to conceal it.

This hosting change is an implementation requirement, not authorization to modify protected shared ingress or live infrastructure. Prepare the deployment configuration and prove it locally. Apply any separately required host/DNS/TLS authorization to the concrete deployment diff.

## 8. Discount-code policy

### 8.1 Recommended initial policy

Use the existing Django staff administration to create and revoke codes. Start with **percentage discounts only**; one code per order/request, no stacking. Fixed-currency discounts, referral systems and campaign engines are unnecessary for the initial product.

| Property | Proposed default |
|---|---|
| Code format | Random, readable uppercase characters with an SLL prefix; no customer names or personal data. |
| Distribution | SLL copies/sends the code with the invitation or a targeted commercial message using its existing communication process. |
| Customer scope | Bound to the invited legal customer/account. |
| Variant scope | FPGA, ASIC or both, explicitly selected. |
| Benefit | Approved percentage of eligible support subtotal; tax follows approved tax rules. |
| Claim window | **30 calendar days from issue**, with exact expiry displayed to staff/customer. Staff may explicitly choose a different approved period. |
| Uses | **One successfully paid purchase** by default. Concurrent attempts cannot reserve the same remaining use. |
| Combination | One code; no stacking. |
| Revocation | Stops new claims immediately. Existing accepted/issued-offer commitments require an explicit reviewed cancellation/change, not silent repricing. |
| Refund | Does not automatically reactivate the code; staff can issue a replacement. |

Store the discount policy, normalized-code verifier/protected lookup, allowed customer/variants, start/expiry, use limit and status on the backend. Apply rate limits to guessing. The code is a pricing concession, not an access credential: a coupon never bypasses invitation or ASIC approval checks.

Validate the code when applied, then authoritatively when reserving it for a submitted request or payable order. Display invalid/expired/inapplicable messages without disclosing another customer's details. Never remove a previously displayed discount or increase a payable total without showing the revised review and obtaining acceptance.

Discount percentages must be within an approved range strictly between 0% and 100%, and rounded payable amounts must remain above zero and any qualified bank minimum. Any free-support arrangement is separately agreed and handled by SLL outside this paid checkout; do not build an online hour-grant feature for it.

### 8.2 FPGA redemption

Applying a code previews the price; it does not consume a use. On checkout, atomically reserve the use against the immutable order. Successful verified payment consumes it once. A safely cancelled/expired attempt releases the reservation only after the payment outcome is reconciled; an uncertain bank attempt cannot free a code for duplicate discounted purchases.

Price/discount reservations have an explicit deadline matched to the qualified bank checkout lifetime. If a customer accepted and started payment before the coupon claim deadline, preserve that locked order price for that payment window. Do not recalculate an in-flight order from today's coupon status.

### 8.3 ASIC redemption during review

**A valid discount submitted with an eligible ASIC request is reserved for that specific request.** Initial review can finish after the code's original claim deadline without removing the customer's discount.

On approval, carry the reserved percentage/policy into the exact offer and display the resulting final amount and the proposed 14-day offer deadline. The claim deadline concerns new claims; the approved offer establishes its own purchase deadline.

Release the reservation when the request is declined/withdrawn, an unpaid offer finally expires, or the customer abandons an information request under the disclosed request-closure process. Do not expire a valid reservation merely because SLL's own review takes time. Flag pending requests for staff attention after 30 days; this reminder is not a promised response SLA or automatic cancellation. If a request is closed after customer inactivity, notify the customer and retain an auditable reason. Release does not extend the original coupon expiry.

Keep one active reservation and one payable offer revision per request. Material changes require revalidation of eligibility and a revised offer; do not reuse a code for an unrelated request. Once payment is verified, consume the reservation once.

Database transactions, uniqueness rules and appropriate locking must protect limited-use coupons and order/payment state against concurrent submissions. Use the actual PostgreSQL-backed path, not frontend checks. [W5][W11][W12]

### 8.4 Independent clocks

| Clock | Rule |
|---|---|
| Shop invitation | Six calendar months from creation. |
| Coupon | Proposed 30-day deadline for a new eligible claim. |
| Approved ASIC offer | Proposed 14-day deadline from issue, with its reserved discount. |
| Bank checkout/order reservation | Provider-qualified deadline recorded for that payment; not an invented universal duration. |
| Purchased FPGA hours | No expiry under the source policy. |
| Purchased ASIC hours | Recommended no expiry, explicitly adopted in the ASIC terms before sale. |

Invitation validity is not a six-month price guarantee. Preserve already accepted orders/offers; new purchases use the current approved price revision.

## 9. Payment, purchase records and manual support tracking

### 9.1 Reuse the existing payment protections

Use bank-hosted payment so the shop does not collect raw card credentials. Obtain the actual provider integration specification and use its documented authentication, status and retry rules; do not prescribe a signing format or capability the selected bank does not support.

For every paid order, correlate verified merchant/order identity, amount and currency. Use durable payment attempts, reconcile uncertain dispatches, and make order finalization repeat-safe. Payment confirmation, the accepted paid-order record, coupon consumption and the queued transaction confirmation must converge on one durable result despite duplicate submissions, callbacks, retries or process interruption. Preserve the existing archive-before-effect and financial accounting evidence requirements. [W3][W4]

A failed notification/email must not erase a successful payment or create a second order or coupon redemption. Use the existing durable worker/outbox for purchase/request/payment communications, not support-task usage emails. Retain order acceptance holds where the commercial policy requires them; possession of an unverified payment reference alone does not establish an accepted paid purchase.

If payment is duplicated, late, overpaid, underpaid, refunded or charged back, use the existing reconciliation/refund controls. An order that SLL cannot accept needs the approved refund/handling outcome. Duplicate payment observations do not create an extra purchased bundle; make the reconciliation outcome visible to staff so a duplicate is not manually counted as another purchase.

### 9.2 Purchase confirmation and support-team handoff

For the initial SHB release, the shop completes the sale by recording the accepted, verified paid order, issuing its transaction confirmation and making its details available to SLL staff. Do not generate an IP licence, release an IP package, create a reference-design promise or extend existing IP rights merely because hours were purchased.

Each order must identify the customer, unique order/payment reference, FPGA or ASIC variant, bundle quantity, hours purchased in that order, accepted terms and any approved ASIC project/scope. Staff can use the existing paid-order view and ordinary order notification; no new handoff portal, acknowledgement gate, ticketing system or time-management application is required. Email retries must use the same order reference, and staff use that reference to avoid entering a purchase twice in their manual records.

The support team manually adds a new paid purchase to the appropriate customer records and maintains separate FPGA and ASIC hours under their applicable scope. Do not use cheaper FPGA hours for ASIC work or invent transfers across legal entities/projects without an explicit commercial agreement. These are manual support-team operating rules; the shop does not implement a spending/conversion engine or a cumulative balance. Keep any existing historical records intact without requiring new purchases to update an online ledger.

### 9.3 Manual support-time tracking and task emails

**SLL's support team is responsible for tracking used and remaining hours manually. The shop has no support-time accounting role beyond retaining the hours bought in each order.** [U2]

The support team uses its existing internal record, records each support session/task and manually sends the customer an email after the support work. To preserve the attachment's reporting promise, the email contains the task description/reference, hours used for that task, total hours used to date and remaining hours; total hours purchased can be included when useful. The team calculates these values manually. Send the information to the authorized customer contact. These support communications continue independently of shop-invitation expiry. [S1: Clear Hour Tracking; Support Usage Is Recorded; U2]

The current shop scope excludes all of the following:

- An online support-time ledger, automatic hour credits/debits, usage reservations or balance reconciliation.
- Used/remaining-hour calculations, an aggregate customer balance, or an online available/used-bundle calculation.
- A customer dashboard/panel/API for support hours, usage or bundles.
- A staff screen for entering consumed support time or generating task-usage emails.
- Automated support-task emails, low-balance alerts, time-based purchase restrictions, or integrations with a new time-tracking service.

The shop still calculates and shows the hours in the current purchase (`quantity × 10` or `quantity × 25`) and sends ordinary transaction/request notifications. An order confirmation showing purchased hours is not a remaining-balance statement. Nothing in checkout waits for the support team to update its manual record.

The support team monitors remaining hours, agrees substantial work/budgets with the customer, and arranges a top-up when needed through its normal communication. Do not turn those manual procedures into new software workflows or launch gates.

The source does not settle rounding/minimum charges, multiple engineers in a meeting or unattended tool-runtime charges. Adopt and disclose the ordinary time-charging convention in the service terms before a paid purchase. The support team applies it manually; no online calculation engine is required. Keep unusual charges unavailable unless separately agreed before that work. These are commercial/service decisions, not additional shop implementation tasks.

### 9.4 Refunds and manual-record corrections

Preserve the attachment's conditional refund wording; do not turn it into an unconditional no-refunds rule. Keep the shop's financial refund/chargeback record linked to the original order with its amount, status and reason. If the decision depends on unused hours, staff consult the support team's manual records first; the shop cannot infer unused time from the original purchased quantity.

After a refund, chargeback or correction, the responsible staff member informs the support team, which adjusts its manual record as appropriate under the approved policy. Do not implement an automatic time-ledger reversal, remaining-hour calculation or balance synchronisation. Preserve the financial history and actual work records, and handle disputed/consumed-hours cases through staff review without inventing a debt settlement rule.

## 10. Policy reconciliation and missing ASIC terms

### 10.1 Preserve the source accurately

| Source term | Required treatment |
|---|---|
| Ten-hour FPGA bundles, multiple quantities and later top-ups | Preserve for FPGA. Add 25-hour ASIC bundles through the new variant policy. |
| Non-expiring purchased FPGA hours | Preserve regardless of invitation/coupon expiry. Recommend the same ASIC term. |
| Task-usage email and support records | Support team maintains the record, calculates time used/remaining and sends the email manually; no shop ledger or customer balance panel. |
| SLL-IP-related integration, configuration, simulation, timing and debugging | Preserve the scope; do not widen to unrelated customer/third-party design work. |
| Supported FPGA families; other devices by agreement | Preserve as approved compatibility data. |
| Technical meetings and engineering investigation can consume hours | Preserve; disclose the ordinary debit/rounding convention in the terms accepted before purchase. |
| Routine administration not normally charged | Preserve; make initial ASIC feasibility review uncharged as the proposed launch policy. |
| No guaranteed outcome or SLA | Preserve; separately agreed commitments must appear in the relevant offer. |
| Excluded new IP, major functionality, unrelated RTL/IP, full system development, PCB design/layout, signal integrity, certification, on-site/travel/hardware and separate development | Preserve unless separately agreed in writing. |
| Confidentiality and customer ownership of submitted material | Preserve; restrict access and use to the support relationship. |
| No transfer of SLL IP rights through support purchase | Preserve; examples/patches remain governed by applicable licences. |
| Customer responsibility for final design, validation and suitability | Preserve without implying that buying hours provides sign-off or certification. |
| Refunds normally restricted after availability, subject to law/terms | Finalize and link the applicable policy; never encode an absolute waiver. |
| Tax, privacy, compliance and order acceptance clauses | Finalize actual applicable rules and references; do not assume a universal VAT/GDPR result from the draft alone. |

### 10.2 Add a concise ASIC supplement

The adopted ASIC policy must state: 25-hour bundles; approved rates/currency; reviewed SLL-IP/project scope; request-only first stage; customer acceptance before payment; a completed purchase only after verified payment and order acceptance; the selected no-expiry rule; separate FPGA/ASIC hours maintained manually by the support team; manual usage-report emails; availability/prerequisites; no implied complete-chip development, tape-out, sign-off, foundry/EDA access or resolution guarantee; the normal exclusions, confidentiality, ownership and customer responsibilities; and how out-of-scope work is separately agreed. It must not promise an online balance or usage panel.

Initial request acknowledgement is not a purchase contract or a promise to provide the requested support. Do not obtain a supposed purchase acceptance at Submit Request and then change the actual offer without another acceptance at checkout.

### 10.3 Business, privacy and tax details

Use the existing business-customer checkout scope. The attachment says primarily business customers; do not infer that it settles every jurisdiction's classification. Preserve the previously agreed B2B launch restriction where already approved and make it clear in the terms. Do not activate a consumer flow as an incidental consequence of this revision.

Record acceptance of the applicable purchase/support/refund terms separately from acknowledgement of the Privacy Policy. Do not make optional marketing consent a purchase requirement. Collect only relevant billing/contact/support data, keep confidential technical material out of public builds and ordinary logs, and apply the approved retention/access rules. Preserve purchase/financial history and the support team's manual records without using an expiring invitation as the retention timer. This does not require importing manual usage records into the shop.

The seller's legal entity, invoice details, territories, applicable taxes and privacy/refund terms must be the actual approved SLL configuration. Country/tax exceptions can hold the affected transaction. This proposal does not determine Georgian, EU or other tax/legal treatment.

## 11. Minimal administration and data changes

Extend existing models and staff screens instead of creating a second commerce engine:

| Logical record | Minimum addition or use |
|---|---|
| Product / variant / approved offer revision | Product title, two variant IDs, hours per bundle (10 or 25), workflow, approved rates/currency, policy references and approval provenance. |
| Invitation | Token digest, customer/eligibility/mode scope, created/expires/revoked timestamps, issuer and audit reference. |
| ASIC support request | Customer details, scoped help description/context, requested quantity, review state, reviewer and revision history. |
| Approved ASIC offer | Immutable customer/request/scope, quantity, price/discount/tax, policy versions and validity. Reuse the existing quote model. |
| Discount and reservation | Benefit, scope, claim deadline, use limits, status and one atomic association to the relevant request/order. |
| Order / order line / acceptance / payment attempt | Existing immutable purchase, financial and acceptance records, with customer, variant, quantity, hours purchased in this order and applicable ASIC scope/offer. No used/remaining-hour fields or cumulative support balance. |
| Audit / transaction notifications | Existing issuer/reviewer/order/payment/coupon evidence and retryable purchase/request mail. Support-task emails are sent manually outside the shop. |

Staff need to issue/revoke invitations, create/revoke discounts, review ASIC requests, issue offers, inspect paid orders and handle payment exceptions. Reuse established staff MFA, recent verification, least-privilege and audit controls. Do not build a support-time entry screen, balance panel or customer support portal. Manual time tracking and task emails remain the support team's existing responsibility outside the shop.

Product copy and policies remain Markdown-editable. Compile a validated server catalog from the approved source so frontend and backend use the same version. Treat prices and commercial flags as approved data, not a way for a content edit to bypass approval. Keep invitation secrets, coupon state, customer/order records and the team's manual support records out of Markdown/Git/public assets.

## 12. Implementation sequence for Codex

1. **Reconcile the current worktree once.** Read applicable AGENTS instructions and current active state. Identify reusable catalog, order, access, quote, payment, staff and transactional-worker components. Preserve uncommitted and subsequent work; do not reset to the historical audit commit.
2. **Update active scope once.** Register revision 1.1 and its source precedence. Mark IP-only work and automated support-time accounting/usage-email/customer-panel work explicitly deferred from SHB launch, retain historical phase/task IDs and evidence, and keep shared security/recovery gates. Re-scope requirements and dedicated tests that exist solely for those deferred time-tracking features; do not retain them as mandatory SHB launch blockers. Update the existing ROADMAP, STATE, PROJECT, HANDOFF and state.json consistently; avoid a replacement master plan.
3. **Implement one product and both forms.** Add the exact labels, 10/25-hour quantities, minimum common fields, ASIC triage fields, server rules and no-JavaScript behavior. Remove the IP product from all active discovery/purchase entry points while preserving old records.
4. **Implement invitation enforcement and private delivery.** Gate actual storefront responses and APIs; prove origin/alternate-route denial and precise six-month expiry. Prepare deployment changes within the isolated shop components.
5. **Connect real application workflows.** Reuse immutable offers/orders and the bank abstraction; implement FPGA checkout, ASIC review/offer/payment, coupon reservation, repeat-safe paid-order finalization and transaction/request emails. Ensure staff can reliably see customer, variant, purchased quantity/hours and applicable ASIC scope using the existing order view/notifications. Do not implement time-ledger updates or task-email generation. Exercise with unmistakably synthetic development data until real commercial/provider configuration is ready.
6. **Verify and prepare activation.** Run focused functional/security/concurrency tests, the affected integration checks and required existing release gates. Maintain one short register of actual external blockers. Supply a usable local demonstration and full commands, then proceed with the next authorized unblocked work.

Unknown numerical rates or bank access block affected live operations, not schemas, local UI, workflow implementation or synthetic demonstrations. A missing ASIC paid-offer approval must not block an otherwise approved FPGA path; request-only ASIC intake can operate only when its own privacy/intake and operational prerequisites are ready.

Retain the 26 October execution lesson: distinguish implementation from synthetic evidence and genuine external qualification. Do not spend another cycle repeatedly auditing completed work or expanding rehearsal features that do not close a current requirement. Repair previously reported test/CI defects only if still present and relevant. Preserve meaningful checks rather than weakening them to obtain a pass. [P3]

## 13. Focused acceptance criteria

Tests below address the actual revised risks. Reuse existing tests and run order/payment/coupon concurrency cases against PostgreSQL with appropriate transaction-test support; SQLite-only checks do not establish row-lock correctness. Automated time-debit/balance and task-email tests are not launch gates for this release. Consult documentation matching the repository's Django version. [W11][W12]

| ID | Scenario | Required result |
|---|---|---|
| SHB-01 | Load active shop with valid access | Exactly one product and the two exact requested variant labels. |
| SHB-02 | Visit old IP route or submit old IP SKU | No new IP sale; existing orders/history and contractual obligations remain intact. |
| SHB-03 | FPGA quantity 1 and 3 | 10/30 hours and authoritative matching prices. |
| SHB-04 | ASIC quantity 1 and 2 | 25/50 requested hours and Submit Request; no initial payment or completed purchase. |
| SHB-05 | Invalid quantity, forged price/hours/discount/customer ID | Backend rejects or derives trusted values; no bypass. |
| SHB-06 | Common form, same-phone choice, conditional tax fields | All six requested fields supported with minimal repetition; no unrelated engineering dossier. |
| SHB-07 | Eligible FPGA purchase and later top-up | No routine engineer approval; each accepted paid order records its own purchased hours once and is available to staff; no online balance update. |
| SHB-08 | Unapproved ASIC checkout/API; altered approved scope | Payment blocked; material change requires a new matching approval/offer. |
| SHB-09 | ASIC approve / clarify / decline / withdraw | Correct state, customer notice and discount reservation treatment; no completed purchase before accepted verified payment. |
| SHB-10 | Base URL, deep links, static JSON/assets, origin, alternate host | No protected shop data without valid access; no public-origin bypass. |
| SHB-11 | Invalid/revoked/expired token or surviving browser cookie | Denied using server state, including the next request after revocation. |
| SHB-12 | Exactly at expiry, month-end and leap year | Correct six-calendar-month rule; no restart from visits or browser-clock changes. |
| SHB-13 | Valid link reused / scanned by email software | Reuse allowed; GET has no commercial/message side effects. |
| SHB-14 | Token leakage, caching, different customers and changed contact email | No raw token in normal logs/referrers/bank URLs; no shared-cache or cross-customer/private-data exposure; entering an email does not replace the company's authorized contact. |
| SHB-15 | Coupon wrong customer/variant, expired, revoked or stacked | Rejected server-side; no access/approval bypass. |
| SHB-16 | Concurrent one-use coupon claims | At most one live reservation/redemption; Apply alone consumes none. |
| SHB-17 | ASIC submitted before coupon expiry, reviewed afterward | Discount reservation survives SLL review and appears in the dated offer. |
| SHB-18 | Declined/withdrawn/expired unpaid offer | Reservation released under policy without extending claim expiry; uncertain payments reconciled first. |
| SHB-19 | Forged browser success or unauthenticated bank callback | No paid status, accepted purchase or paid-order confirmation. |
| SHB-20 | Duplicate/out-of-order bank messages and process interruption | Correct final bank/order state, one order finalization, one coupon redemption and repeat-safe transaction notifications carrying the same order reference. |
| SHB-21 | Uncertain payment dispatch or duplicate real payment | Reconcile; no blind second charge or duplicate purchase; staff can identify the original order. |
| SHB-22 | Payment notification or ASIC review after invitation expiry | Existing work reconciles/continues; no new checkout through expired access. |
| SHB-23 | Temporary transaction-mail failure | Order/payment/coupon state retained; paid order remains visible to staff and notification retries do not create a second purchase. |
| SHB-24 | Manual support-tracking boundary | No online time-ledger mutation, available/used/remaining-hour calculation, support/bundle panel or API, staff time-entry workflow or automated task-usage email. Purchased-hours display remains per order. |
| SHB-25 | Refund/chargeback with unused or consumed hours | Financial change linked to original order; staff consult manual usage records where needed and inform the support team; no automated time adjustment or erased financial history. |
| SHB-26 | Invite expires with unused purchased hours | Purchased support remains valid under its terms; support team continues manual tracking and task emails independently. |
| SHB-27 | JavaScript unavailable; keyboard/mobile flow | Same backend access, price, validation and approval rules; usable forms and clear errors. |
| SHB-28 | Restore/replay within existing recovery qualification | Invitations retain original expiry/revocation; reconcile post-backup financial/order/coupon events before reopening; preserve order references so staff do not count a replay as a new purchase. |
| SHB-29 | Missing rates/policies/provider authority | Affected live action fails closed; local implementation still runs with explicit synthetic data. |
| SHB-30 | Deployment review | All protected existing services unchanged; required isolated/off-host qualification retained. |

A link can never retract content that a recipient already copied or photographed. SHB-14 tests fresh unauthorized retrieval, cache leakage and accidental disclosure, not an impossible remote erasure guarantee.

## 14. Commercial inputs and release boundaries

### 14.1 One concise support-offer decision record

Reuse any already approved applicable values. Otherwise collect these in **one versioned support-offer record**, with real approver, approval date, scope and source evidence. Do not create multiple approval packages for the same decision or ask for obsolete IP-sale prices/rights.

| Input | Needed before | Work that continues without it |
|---|---|---|
| FPGA hourly rate, ASIC hourly rate, currency and rate authority | Showing a payable offer / accepting money for that variant | Quantity math, catalog schema, forms, synthetic demonstrations. |
| Final SHB terms, privacy/refund references and ASIC supplement | Relevant live intake/offer/purchase | Policy rendering/versioning and acceptance mechanisms. |
| ASIC no-expiry adoption, scope and separate manual FPGA/ASIC tracking | Selling ASIC hours | Review flow and disabled/sample offer logic. |
| Ordinary engineering-time charging unit and minimum/rounding convention, applied manually by the team | Issuing a payable offer / selling hours | Shop/order implementation and transaction notifications; no online time-calculation work. |
| Unusual multiple-engineer/tool-runtime charges and substantial-task budget authorization | Performing the affected work; keep unagreed unusual charges unavailable | Ordinary sales and work under the already approved standard charging rule. |
| Seller invoice identity, tax/territory and applicable compliance rules | Live acceptance/payment in the relevant case | Conditional fields, tax interfaces and explicit unsupported-case holds. |
| Customer/SLL-IP eligibility and reviewer ownership | Issuing an automatic-purchase invite / approving ASIC work | Staff workflows and synthetic eligible/ineligible cases. |
| Adopted discount defaults and authority | Issuing real discount codes | Coupon/reservation implementation and tests. |
| Selected bank specification, merchant/currency configuration and sandbox/production readiness | Real payment integration qualification / live charges | Adapter interfaces and local synthetic end-to-end flow. |
| Existing approved mail route, secure deployment/ingress and required release evidence | Live operation | Templates, local/private deployment artifacts and normal implementation. |

Do not interpret a technical review as commercial approval. Conversely, once a standard support offer is genuinely approved, do not request a fresh approval for each ordinary eligible FPGA order.

### 14.2 Protected infrastructure

Preserve the prior explicit protection of Stalwart, WebAdminProxy, Plesk/WordPress, existing PostgreSQL, Prometheus, Grafana/Grafana-TLS, Blackbox, Alertmanager, MicroVMs, NetBird, Matrix and all other pre-existing or uncertain resources. Maintain a separate shop database and resource boundaries.

No blanket NixOS activation, protected proxy reload, service restart, firewall/DNS/TLS change, production migration, live bank/mail action or paid infrastructure purchase is authorized merely by this document. Prepare concrete artifacts and use actual existing/scoped authority for each live action. If shared routing cannot reach the new shop without a protected change, keep that activation dependency explicit and continue unaffected work. Disruptive tests remain off-host. [P1][P2][P3]

## 15. Copy-ready implementation instruction

> Apply revision 1.1 of this 30 October 2026 SHB proposal to the current 014-Shop worktree and continue implementation. Keep Supporting Hours Bundle as the only visible product, with the exact FPGA/ASIC variant labels, 10/25-hour bundle sizes, automatic eligible FPGA checkout and reviewed ASIC offers. Implement the shared minimum form, server-enforced six-calendar-month invitations, private storefront delivery, the proposed scoped discount lifecycle and repeat-safe order/payment/coupon handling. Record only the bundles and hours bought in each order, send ordinary transaction/request confirmations and make paid-order details available to staff. The support team manually tracks used/remaining hours and manually sends every support-task email outside the shop. Do not implement an online time ledger, hour-credit/debit integration, balance/usage calculations, staff time-entry workflow, automatic task emails or customer support/bundle panel, and remove their dedicated requirements/tests from this release's mandatory gates through the documented scope change. Preserve historical data/code, the attached FPGA policy's no-expiry terms, existing accepted obligations and shared payment/security/recovery/protected-service controls. Treat the ASIC supplement, rates and unresolved commercial values as explicit pending live configuration; do not fabricate approval or block unrelated local work. Defer IP-only sale requirements without deleting history or rebuilding the shop. Update existing planning/state files once, implement the next usable batch, run focused and required checks, and report actual behavior, executed tests, synthetic versus real evidence and the remaining specific external inputs. Give full reproducible commands. Do not stop after another planning document.

The completion report should identify changed current files, demonstrate both paths locally, state which commercial/configuration records were used, and make clear which live qualifications remain. This proposal is a handoff; it is not evidence that the repository or deployed shop has already been changed.

## 16. Sources and verification basis

### Project and supplied sources

- **[P1]** SLL-xSPI-MC-Shop-Proposal-2026-10-21.md — selected Astro/Django/PostgreSQL/rootless-Podman architecture, independent shop database, protected infrastructure and commercial/activation separation. [Saved proposal](https://chatgpt.com/library?file_id=libfile_d78f0fb452d48191897e936c894b04b7&account_id=personal).
- **[P2]** 014-Shop-Board-Support-Amendment-2026-10-26.md, final revision 2 — simple checkout, SLL-only support, later engineering intake, preserved top-ups and protected-host rules. Its automated support-ledger requirement is superseded for this release by [U2]. [Saved amendment](https://chatgpt.com/library?file_id=libfile_80b7e6dd764c8191b003ef4089b27e40&account_id=personal).
- **[P3]** 014-Shop-Repository-Review-and-Codex-Prompt-2026-10-26.md — historical audit and implementation-priority instruction; reviewed commit identified in section 1. [Saved review](https://chatgpt.com/library?file_id=libfile_a80a3f44aa54819184c9bf8d54d447f0&account_id=personal).
- **[S1]** User attachment SLL_10_Hour_Support_Package(1).md — full original text in Appendix A. SHA-256 of the supplied bytes: `5ae1936335c8bd5e2b91e7bab7045e1279ac38ef2b6d47eed67a981496df3e5a`.
- **[U1]** User direction dated 30 October 2026 in Synaptic-Online-Shop — product change, exact names, six-month access, bundle sizes, ASIC review and common form/discount requirements. The requirements are reproduced in the operative sections above.
- **[U2]** User follow-up dated 30 October 2026 — no online available/used-time calculations or customer balance/bundle panel; the support team keeps remaining time manually and emails the customer after each support session/task. Revision 1.1 applies this instruction throughout and defers the earlier automated time-accounting requirements.

### Primary technical references checked for this revision

These sources support the stated technical boundaries. They do not approve SLL commercial terms. Numerical defaults and workflow choices identified as recommendations are this proposal's design decisions.

- **[W1]** [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) — server/resource authorization, including static resources.
- **[W2]** [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) — random credentials, protected storage/cookies and server-managed validity.
- **[W3]** [OWASP Third Party Payment Gateway Integration](https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Payment_Gateway_Integration_Cheat_Sheet.html) — authoritative amounts, payment verification, correlation and repeat-safe fulfilment.
- **[W4]** [OWASP Webhook Security](https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html) — authenticated provider events, retries, ordering and durable handling.
- **[W5]** [OWASP Business Logic Security](https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html) — explicit workflow rules, trusted calculations and concurrent entitlement changes.
- **[W6]** [RFC 9076, DNS Privacy Considerations](https://www.rfc-editor.org/rfc/rfc9076.html) — disclosure/observation implications of DNS names.
- **[W7]** [Amazon Route 53 domain-name and wildcard rules](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DomainNameFormat.html) — a wildcard replaces a whole leftmost label.
- **[W8]** [RFC 9525, Service Identity in TLS, section 6.3](https://www.rfc-editor.org/rfc/rfc9525.html#section-6.3) — certificate wildcard matching.
- **[W9]** [RFC 6750, Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html) — the possession-based property of bearer credentials; this proposal does not require implementing OAuth.
- **[W10]** [OVHcloud Object Storage static website documentation](https://docs.ovhcloud.com/en/guides/storage-and-backup/object-storage/s3-website) — its public-read website configuration.
- **[W11]** [Django database transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) — transactional operations; use the version corresponding to the repository.
- **[W12]** [Django QuerySet select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update) — database locking and test limitations; use the version corresponding to the repository.

## Appendix A — Original attachment, preserved as historical source

**This appendix is the unchanged FPGA-only source, not the revised storefront copy.** Its old title, Add to Cart placeholders, FPGA-only quantities and unresolved price/legal references must not override the operative revision. Codex should preserve the source, produce separate versioned SHB copy/ASIC supplement and validate commercial approval before publication.

The source's usage-record and email promises are fulfilled manually by the support team under revision 1.1; they do not require a software ledger, an automated task email or an online balance panel.

The supplied UTF-8 document follows verbatim inside a fence. Its original file hash is recorded above; the fence itself is not part of the original file.

````markdown
# FPGA IP Technical Support Package – 10 Hours

Get direct engineering support for integration, configuration, simulation, timing, hardware bring-up and troubleshooting of supported SLL FPGA IP products.

Each package includes **10 Engineering Support Hours**.

You may purchase multiple packages according to your expected support requirements. Support hours **do not expire** and remain available until used.

---

## Purchase Support Hours

**10-Hour Support Package**  
**€[PRICE] + applicable VAT**

**Quantity:** [ − ] **1** [ + ]

**Total Support Hours:** 10 hours  
**Total Price:** €[PRICE] + applicable VAT

**[ ADD TO CART ]**

| Quantity | Total support hours |
| --- | --- |
| 1 | 10 hours |
| 2 | 20 hours |
| 3 | 30 hours |
| 5 | 50 hours |

Additional support packages may be purchased at any time.

<!-- Store implementation: quantity must be a positive integer. Update total support hours to quantity × 10 and the subtotal to quantity × package price whenever quantity changes. The controls shown above are placeholders for the store interface. Replace [PRICE] before publication. -->

---

## Direct FPGA Engineering Support

Use your available support hours whenever assistance is required.

### Typical Support Activities

- IP integration assistance
- IP configuration
- Simulation support
- Testbench assistance
- Timing and constraint review
- FPGA implementation support
- Memory-interface configuration
- Hardware bring-up assistance
- Analysis of simulation logs and reports
- Analysis of timing reports
- Investigation of unexpected IP behaviour
- Review of relevant customer integration RTL
- Assistance reproducing reported issues
- Guidance regarding supported memories and FPGA configurations
- Technical meetings and remote engineering sessions

## Key Benefits

### Direct Engineering Access

Communicate directly with engineers familiar with the SLL IP and supported memory interfaces.

### Flexible Usage

Use your support hours when required. There is no requirement to consume the hours within a particular period.

### No Expiry

Purchased support hours remain available until they are used.

### Buy What You Need

Purchase one or multiple 10-hour packages depending on your project requirements.

### Clear Hour Tracking

After each completed support task, you will receive an email showing:

- A description or reference to the support task
- The number of support hours used for that task
- The total support hours used to date
- The remaining support-hour balance

This provides a clear record of support usage throughout your project.

## Supported FPGA Families

### Altera / Intel FPGA

- Cyclone 10 LP (C10LP)
- MAX 10
- Cyclone 10
- Cyclone 10 GX
- Cyclone V
- Stratix 10
- Agilex 3
- Agilex 5

### AMD / Xilinx

- Series 7
- UltraScale
- UltraScale+

### Microchip

- PolarFire
- PolarFire SoC

Support for other FPGA families or devices may be available by prior agreement.

## How It Works

### 1. Purchase Your Support Hours

Select the number of 10-hour support packages required and add them to your cart.

For example, purchasing three packages provides a total support balance of **30 engineering hours**.

### 2. Submit a Support Request

Contact SLL with a description of the issue or assistance required.

Where applicable, please provide relevant information such as:

- FPGA device
- FPGA development-tool version
- SLL IP product and version
- IP configuration
- Relevant logs
- Timing reports
- Simulation waveforms
- Description of expected and observed behaviour
- Relevant design files or reduced test case

### 3. Engineering Support Is Provided

SLL engineers will investigate the request and provide technical assistance as appropriate.

Support may be provided through:

- Email
- File exchange
- Remote technical meetings
- Design or report review
- Simulation or debugging work

### 4. Support Usage Is Recorded

After the support task has been performed, SLL will send an email confirming the support usage.

The email will include:

**Hours used for the current task:** X hours  
**Total hours used to date:** X hours  
**Remaining support balance:** X hours

This email provides the customer with an ongoing record of support-hour consumption.

#### Example Support Usage Email

> **Task:** PolarFire timing investigation  
> **Hours used for this task:** 1.5 hours  
> **Total support hours purchased:** 30 hours  
> **Total support hours used:** 7.5 hours  
> **Remaining support balance:** 22.5 hours

## What Counts as Support Time?

Engineering support time may include time spent:

- Investigating a reported problem
- Reviewing technical documentation
- Reviewing customer-provided RTL relevant to the SLL IP
- Reviewing logs and reports
- Analysing simulation results
- Reproducing an issue
- Performing simulations
- Reviewing timing results
- Preparing configuration recommendations
- Preparing technical responses
- Participating in technical meetings
- Preparing examples directly related to the support request

Routine administrative communication is not normally charged as engineering support time.

## What Is Not Included?

Unless separately agreed in writing, the support-hours package does not include:

- Development of new IP products
- Major new functionality added to an existing IP product
- Development of unrelated customer RTL
- Full FPGA-system development
- Debugging unrelated third-party IP
- PCB design
- PCB layout
- Signal-integrity analysis
- Product certification
- Functional-safety certification activities
- On-site engineering services
- Travel
- Hardware purchases
- Development work requiring a separate engineering project

Where a request falls outside normal technical support, SLL may propose a separate engineering quotation before proceeding.

---

## Frequently Asked Questions

### How many support hours do I receive?

Each package provides **10 engineering support hours**. You may purchase more than one package. For example, a quantity of 4 provides a total of **40 support hours**.

### Do my support hours expire?

No. Purchased support hours **do not expire** and remain available until used.

### Can I purchase additional support hours later?

Yes. Additional 10-hour packages may be purchased at any time. New hours are added to your existing available support balance.

### How do I know how many hours I have used?

After each support task is performed, you will receive an email showing:

- Hours used for the latest task
- Total accumulated hours used
- Remaining support balance

You may also request confirmation of your support balance at any time.

### Are meetings charged against my support hours?

Yes. Technical meetings and remote engineering sessions that relate to a support request are normally counted as engineering support time.

### Are emails charged as support time?

Routine administrative emails are not normally charged. Engineering work required to investigate a question and prepare a technical response may form part of the support time used.

### Can you review my RTL?

Yes, where the RTL is relevant to integrating or troubleshooting SLL IP. A substantial review of an unrelated FPGA design or development of customer RTL may require a separate engineering quotation.

### Can you analyse timing problems?

Yes. Support may include review of timing reports, FPGA constraints, clocking arrangements and implementation issues relevant to SLL IP.

### Is hardware debugging included?

Remote assistance with FPGA and memory hardware bring-up may be provided. PCB design, PCB rework, physical measurements, laboratory testing or on-site debugging are not included unless separately agreed.

### Does purchasing support guarantee that an issue will be resolved?

No. The support package purchases engineering investigation and assistance time.

SLL will use reasonable engineering efforts to assist with the reported problem, but resolution cannot be guaranteed because an issue may depend on customer RTL, PCB design, third-party components, FPGA tools, device behaviour or other factors outside SLL's control.

### Does this package provide an SLA?

No, unless an SLA has been separately agreed in writing. Purchasing engineering support hours does not by itself guarantee a particular response time or resolution time.

### Can unused hours be refunded?

Purchased support hours are normally non-refundable once the package has been made available to the customer, subject to applicable law and the SLL Terms and Conditions.

---

## Support Usage and Customer Approval

SLL will use purchased support hours only for technical work reasonably associated with customer support requests.

For larger investigations, development activities or work likely to consume a significant portion of the customer's available support balance, SLL may contact the customer before proceeding.

Where the requested activity falls outside the scope of standard support, SLL may provide a separate quotation.

## Confidentiality

Technical information supplied by customers for support purposes will be treated as confidential in accordance with the applicable Terms and Conditions and any Non-Disclosure Agreement in place between the customer and SLL.

Customer information will be used only as reasonably necessary to provide the requested support and operate the associated customer relationship.

Customers should not submit passwords, private keys, authentication credentials or unrelated confidential personal information.

## Customer Design Files

Customers may provide technical files reasonably necessary for investigation of a support request, including:

- RTL source files
- FPGA project files
- Simulation files
- Waveforms
- Timing reports
- Build reports
- Memory configuration information
- Relevant schematics
- Diagnostic logs

Such files remain the property of the customer or their respective owner. Submission of customer files for technical support does not transfer ownership of those files to SLL.

## Data Protection and GDPR

Personal information provided when purchasing or using the support service is processed in accordance with applicable data-protection legislation, including the **EU General Data Protection Regulation (GDPR)**.

Information processed may include:

- Customer name
- Company name
- Business email address
- Telephone number
- Billing information
- VAT information
- Support correspondence
- Support history
- Names and contact details contained in technical communications

Personal data may be processed for purposes including:

- Processing customer orders
- Processing payments
- Providing purchased support services
- Communicating with customers
- Maintaining records of purchased and consumed support hours
- Maintaining transaction and accounting records
- Meeting legal, accounting and tax obligations
- Protecting the security of SLL systems and services

Further information regarding data processing, retention, customer rights and contact details should be provided in the SLL **Privacy Policy**.

By purchasing the service, customers acknowledge that information necessary to administer and provide the support service will be processed for these purposes.

## Support Records

SLL may retain records relating to the purchase and consumption of support hours, including:

- Number of hours purchased
- Number of hours consumed
- Support request references
- Dates of support activities
- Description of work undertaken
- Customer correspondence

These records may be retained for legitimate business, contractual, accounting, legal and support-history purposes in accordance with the applicable Privacy Policy and retention requirements.

## Intellectual Property

Purchase of engineering support hours does not transfer ownership of any SLL intellectual property.

All SLL:

- IP cores
- RTL
- Software
- Documentation
- Designs
- Examples
- Scripts
- Methodologies
- Technical material

remain subject to the applicable intellectual-property rights and licence agreements.

Where SLL provides examples, modifications, patches or other technical material during a support activity, use of such material remains subject to the applicable SLL licence terms unless otherwise agreed in writing.

## Customer Intellectual Property

Technical material supplied by the customer remains the property of the customer or its respective owner.

Providing such information to SLL for technical-support purposes does not grant SLL ownership of the customer's design or intellectual property.

## Third-Party Products and Trademarks

Intel, Altera, AMD, Xilinx, Microchip and other product and company names referenced on this page may be trademarks of their respective owners.

References to third-party FPGA devices, memories, software or development tools are made solely to describe compatibility and technical support capabilities.

SLL is an independent supplier unless otherwise expressly stated.

Purchase of SLL products or services does not imply endorsement, certification or responsibility by any third-party manufacturer.

## Customer Responsibilities

The customer remains responsible for the design, verification, validation and suitability of its final product.

This includes responsibility for:

- Overall FPGA-system design
- RTL not supplied by SLL
- FPGA implementation
- PCB design
- Hardware design
- System verification
- Production testing
- Product qualification
- Regulatory compliance
- Safety requirements
- Functional-safety requirements
- Determining whether the SLL IP is suitable for the customer's intended application

Technical recommendations provided during support should be verified by the customer within its own final design and operating environment.

## Limitation of Support Scope

SLL technical support is intended to assist the customer with the use and integration of SLL IP.

Support does not constitute a guarantee that:

- Customer hardware will operate correctly
- Customer RTL is error-free
- Third-party devices will operate as expected
- A particular FPGA implementation will meet timing
- A customer product will pass regulatory or safety certification
- A technical problem can be resolved within a specified number of support hours

## Taxes and VAT

Prices displayed on this website may exclude VAT unless otherwise indicated.

Applicable VAT or other taxes will be determined according to the customer's location, tax status and applicable legislation.

Business customers may be requested to provide a valid VAT number where applicable.

## Business Customers

This product is intended primarily for companies, organisations and professional customers purchasing SLL products and services for business purposes.

## Export Control and Sanctions Compliance

SLL products, technical information and engineering services may be subject to applicable export-control and sanctions regulations.

Customers are responsible for ensuring that their purchase, access and use comply with applicable laws.

SLL reserves the right to decline or suspend a transaction where providing a product or service would breach applicable legal or regulatory requirements.

## Order Acceptance

Submission of an online order does not necessarily constitute final acceptance of that order.

SLL reserves the right to verify:

- Customer identity
- Company information
- VAT information
- Payment
- Product eligibility
- Export-control or sanctions requirements

before accepting or fulfilling an order.

If an order cannot be accepted, any payment received for that order will be handled in accordance with the applicable Terms and Conditions and payment-provider rules.

## Terms of Purchase

By placing an order for an SLL Technical Support Package, the customer confirms that they have read and agree to the applicable:

- Terms and Conditions
- Privacy Policy
- IP Licence Agreement, where applicable
- Refund and Cancellation Policy

- [ ] **I have read and agree to the Terms and Conditions and Privacy Policy.**

**[ ADD TO CART ]**

<!-- Publication note: add links to the final policies and applicable licence agreement. This file preserves the product-page draft; the policy references and draft legal wording require finalisation before launch. -->
````
