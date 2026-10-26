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
