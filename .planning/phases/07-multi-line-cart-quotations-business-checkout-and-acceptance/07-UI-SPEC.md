# Customer checkout demo UI contract — 2026-10-26

User requested production-like but simple demo screens to reduce input mistakes. Applies to existing access, business, cart and checkout screens and the new synthetic acceptance/payment screen under07-03. Inline UI research/checking; no external design service or agent dispatch.

Reuse public index.astro tokens: cream #f6f5ef, ink #132f31, primary green #275b4a, muted green #527867, pale summary #e5ecdf, border #cad5cb, focus copper #ad5e2f. System font stack, no remote fonts/images/scripts. Body16px, small14px, page title32–44px, spacing8/16/24/32px, content1180px maximum, controls44px minimum height. Two-column content/help layout collapses at760px. Visible focus/labels, real fieldsets/legends and semantic alert/status messages; readable disabled states.

Shared SLL/xSPI-MC masthead, persistent local-demo notice, access/business/cart/review/payment navigation with current step, content panel and concise support/rights reminder. Preserve all19 business groups and partial saves. Mark required-for-checkout groups and explain helper copies, defaults and pending country/tax choices; report specific missing business labels at checkout. Never make optional/country-pending fields mandatory. Use familiar field labels, human-readable money and clear action buttons. No project-stage or engineering questionnaire.

Acceptance screen shows frozen cart/business revisions, all lines, staged obligation and clearly labelled document fixtures. Explicit unchecked rehearsal-only declaration; one accept, one simulated payment, lookup-only uncertain state. Distinct illustrative deadlines. Actual legal acceptance, charges, licence and support effects remain disabled.

One fixed public CSS asset under /purchase/assets/shop.css, served locally by Django and preserved by the demo proxy. Add only its exact path to retained-source allowlist. CSP permits self stylesheet only; no inline-style/script relaxation. Keep CSRF, cookie, origin, no-store and resource authorization controls.

Verification: rendered shared shell and labels, CSS HTTP/content type/privacy boundary, CSP self stylesheet, backend form/acceptance tests and real proxy form checks. Visual appearance/responsiveness remains a human browser-review item until reviewed; no screenshot or accessibility certification is invented.

## Inline UI contract check

| Dimension | Result and evidence |
|---|---|
| Design-system consistency | Public shop tokens reused; no new UI dependency |
| Hierarchy/navigation | Shared masthead, current-step navigation, content/help panels and clear primary actions |
| Interaction states | Partial saves, labelled pending/disabled real actions, named missing fields, synthetic confirm/pay/captured/uncertain states |
| Accessibility structure | Native labels/fieldsets, focus styling, skip link, semantic status/alerts; actual accessibility review pending |
| Responsive behavior | Two-column layout and business grid collapse at760px; actual viewport review pending |
| Copy and scope | Synthetic label persists; required vs optional/pending guidance; readable EUR; no engineering questionnaire |
| Implementation/privacy | Self-only CSS, explicit retained-source path, no scripts/external assets; CSRF/origin/resource checks pass |

Structural verification passes in the13 focused tests and full367 backend lane. Visual/human browser review remains pending; this is not production UI acceptance.

Phase10 continuation adds synthetic licence/support grant and per-line initial/later completion controls to the same page. Show exact package/hour/second totals, no expiry, remaining later obligation and explicit actual-spending-disabled notice. Status/actions remain synthetic; no technical file upload or actual download. Latest full378/final focused11 and live proxy50 structural checks pass; visual/browser review remains pending.

Phase10-02 support continuation reuses this shell for private balance/reservation/release and scoped staff work/correction/statement forms. Show granted/reserved/spent/available integer seconds and committed revision; label simulation and actual-spending-disabled scope. Require native labels/whole-second bounds, clear reservation/work actions and immutable statement revision. Do not expose staff attribution/MFA generations, raw evidence receipts or business details to customers. Focused13/full391 and proxy66 structural checks pass; no new visual/accessibility approval inferred.

Phase10-01 private materials use the same shell: clearly label inert text fixtures, retained stage/revision and outstanding later design, exact staff assignment and owner-only download. Separate a prepare-download form from the one-use two-minute POST download; never put bearer material into links, persistent browser storage or ordinary summaries. Use labelled native stage/fixture selectors and fixed safe filenames, no upload/host/technical questionnaire. Bound and paginate material and assignment lists. Structural package15/proxy88 checks pass; visual/accessibility acceptance remains pending.

Phase10-03 reviewed changes reuse the private shop shell. Offer narrow renewal/rehosting/family/node/production actions against an existing IP line, with no new platform interview, host-ID/key field or upload. Show original/requested scope, committed review revision, review/proposal history and current versus superseded held proposal. Staff controls require exact-case assignment and recent local MFA; "ready for commercial review" never says rights approved. Keep fees/dates/host/overlap/revocation/maintenance pending, higher-volume quotation explicit, and payment/licence activation disabled. Use closed native forms, labels and bounded paging; no script or external asset. Customer summaries omit staff/MFA/archive metadata. Structural tests/demos remain local; visual/accessibility acceptance pending.
