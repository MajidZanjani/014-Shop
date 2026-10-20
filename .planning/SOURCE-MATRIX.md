# Source-to-Requirement Matrix: xSPI-MC

**Source:** October 20 proposal, exact embedded product and new handoff. Inventory below is a verbatim planning reference from the supplied proposal, not approved customer copy or a catalog. All mapped implementation remains pending. The exact original product is separately hash-verified in docs/product-source/.

| Source contract | Primary requirement coverage | Integrated evidence |
|---|---|---|
| Exact source identity and repository scope | SRC-01–SRC-04 | UAT-01 |
| Vendor/family order, term availability, production bands | CAT-02, SHOP-01 | UAT-01–UAT-02 |
| Access counts/rows/server model and host privacy | CAT-02, AUTH-04–AUTH-05 | UAT-03 |
| Thirteen logical configuration controls and reset matrix | SRC-02, SHOP-02–SHOP-03 | UAT-01–UAT-03 |
| Nineteen business groups, two helpers | SRC-02, COM-04 | UAT-01–UAT-02 |
| Four IP declarations and independent marketing | COM-05–COM-06, AUTH-06 | UAT-02 |
| Draft prices/allowances, recurrence and approval | CAT-03–CAT-05, COM-06 | UAT-02–UAT-03 |
| IP quantity one, support quantity, mixed cart | COM-01–COM-02 | UAT-02 |
| Support-only profile, no new IP rights | COM-05, FUL-04 | UAT-02 |
| Payments and complete-window bank reconciliation | PAY-01–PAY-05, BANK-01–BANK-04 | UAT-03–UAT-04 |
| Four deliverables, scoped downloads and manual amendments | FUL-01–FUL-03 | UAT-02–UAT-03 |
| Support grant, reservation, completion, statement and corrections | FUL-04–FUL-06, OPS-04 | UAT-02–UAT-03 |
| Exact domains, Route 53, TLS, static HTTP/publication | HOST-01–HOST-05 | UAT-01, UAT-03–UAT-04 |
| Restore beyond DB point, revoked access and financial effects | OPS-01–OPS-06 | UAT-03–UAT-04 |
| Release readiness and actual authorization/effects | REL-01–REL-04 | Final evidence manifest |

## Exact option inventory (proposal reference)


The following labels and ordering come from the product source. Proposed stable IDs are implementation identifiers, not replacements for the displayed labels. There are **three vendor options and thirteen family options: eight, three and two respectively**. No additional vendor or family is inferred.

### FPGA vendors and families

| Vendor order | Exact vendor label | Proposed vendor ID | Family count |
|---|---|---|---|
| 1 | Altera / Intel FPGA | `altera` | 8 |
| 2 | AMD / Xilinx | `amd-xilinx` | 3 |
| 3 | Microchip | `microchip` | 2 |

| Vendor | Family order within vendor | Exact family label | Proposed family ID |
|---|---|---|---|
| Altera / Intel FPGA | 1 | Cyclone 10 LP (C10LP) | `altera-cyclone-10-lp-c10lp` |
| Altera / Intel FPGA | 2 | MAX 10 | `altera-max-10` |
| Altera / Intel FPGA | 3 | Cyclone 10 | `altera-cyclone-10` |
| Altera / Intel FPGA | 4 | Cyclone 10 GX | `altera-cyclone-10-gx` |
| Altera / Intel FPGA | 5 | Cyclone V | `altera-cyclone-v` |
| Altera / Intel FPGA | 6 | Stratix 10 | `altera-stratix-10` |
| Altera / Intel FPGA | 7 | Agilex 3 | `altera-agilex-3` |
| Altera / Intel FPGA | 8 | Agilex 5 | `altera-agilex-5` |
| AMD / Xilinx | 1 | Series 7 | `amd-series-7` |
| AMD / Xilinx | 2 | UltraScale | `amd-ultrascale` |
| AMD / Xilinx | 3 | UltraScale+ | `amd-ultrascale-plus` |
| Microchip | 1 | PolarFire | `microchip-polarfire` |
| Microchip | 2 | PolarFire SoC | `microchip-polarfire-soc` |

**Coverage decision:** preserve `Cyclone 10 LP (C10LP)`, `Cyclone 10` and `Cyclone 10 GX` as three distinct source options, while marking their coverage relationship unresolved. The source specifically asks whether `Cyclone 10` is a separate licensed option or an umbrella for LP/GX. A unique option ID does not prove unique billable coverage. Until SLL resolves that relationship, a configuration involving unresolved coverage must receive review rather than a guessed additional-family charge. Do not silently merge labels, sell overlapping coverage twice or grant umbrella coverage from a narrower selection. [Source, section 1 and implementation notes](#product-source-snapshot)

### Licence term and use

| Order | Exact option label | Proposed ID | Source availability | Specified scope and remaining boundary |
|---|---|---|---|---|
| 1 | R&D — annual | `rd-annual` | All three listed vendors | Annual research and development licence. Production rights are not included unless expressly granted in the licence agreement. |
| 2 | RDP — yearly | `rdp-yearly` | Altera / Intel FPGA only | Annual research, development and production within the purchased production band, subject to the licence agreement. The source still requires approval of the RDP expansion and precise permitted-use definitions. |
| 3 | Perpetual | `perpetual` | All three listed vendors | Non-expiring licensed rights as defined in the agreement. Production, maintenance, updates and support are not implicitly unlimited. |

Exactly one term is selected. The source's `annual` and `yearly` spellings are retained in their respective labels. Both are annual terms in the source's commercial model; neither establishes automatic renewal. The licence start trigger, end date calculation, renewal process, renewal pricing, and consequences for development access, new production and already deployed products are unresolved. Those consequences must be visible before payment. [Source, section 2, FAQ and annual/perpetual terms](#product-source-snapshot)

### Production bands

Show this selector only when `rdp-yearly` is active, which also requires `altera`.

| Order | Exact band label | Exact production-units label | Proposed ID | Commercial treatment |
|---|---|---|---|---|
| 1 | Band 1 | 1–100 | `units-1-100` | Adjustment is an unresolved price. |
| 2 | Band 2 | 101–1,000 | `units-101-1000` | Adjustment is an unresolved price. |
| 3 | Band 3 | 1,001–5,000 | `units-1001-5000` | Adjustment is an unresolved price. |
| 4 | Higher volume | More than 5,000 | `higher-volume` | Request a quotation; no automatic checkout price. |

The integer ranges avoid overlap at 1,000. The source does not offer a zero-unit RDP band. Do not add one without a commercial decision. These ranges also do not define what a production unit is, which events count it, how projects/products/families are aggregated, the measurement period, reporting obligations, upgrades or rights after expiry. The annual measurement period is explicitly proposed, not settled. Node counts and floating seats are development-access quantities and must remain separate from these production bands. [Source, sections 3–4 and implementation notes](#product-source-snapshot)

### Licence-access options

The source exposes exactly two access-mode choices for Altera / Intel FPGA:

| Order | Exact control label | Cardinality and source requirement |
|---|---|---|
| 1 | Fixed / node-locked licences | Boolean selection; can be combined with floating licences. |
| 2 | Floating licences | Boolean selection; can be combined with fixed licences. |

At least one mode is required for an Altera configuration. An enabled mode needs a positive integer count; an inactive mode has zero count and zero related charge. Fixed access requires one complete host-ID row for every selected fixed node. Floating access is drafted as concurrent seats bound to a licence server, with one server identifier rather than one client identifier for each seat. **The actual licence-manager mechanism, host-ID format, server requirements, redundancy and concurrent-seat semantics still require verification.** [Source, section 4 and selection rules 5–8](#product-source-snapshot)

AMD / Xilinx and Microchip remain first-class vendor options in the catalog. Their access mechanisms are unresolved: do not reuse Altera node charges, assume that their keys are unrestricted, collect speculative NIC fields, or remove them from the proposed product model. A complete configuration for either vendor remains `awaiting_review` until its actual access conditions and offer are approved. A later approved host requirement would be an explicit revision to that vendor's profile.


## Exact field and control inventory (proposal reference)


This is an inventory of the written specification. The bracketed widgets illustrate intended controls; no live requiredness, browser validation or runtime behaviour was inspected. Where the source uses section headings instead of a single input label, the inventory identifies the control by its purpose. Counts below refer to logical definitions and source table rows, not a fixed number of rendered inputs: host rows repeat, addresses expand by country, and several source rows contain more than one value.

### Configuration controls

There are **thirteen logical configuration control definitions**, including the two fields repeated for each fixed host. Generated summaries, prices, row numbers and calculated support hours are outputs, not extra customer inputs.

| # | Source field or control | Proposed type | Visibility / required response | Source illustration or intended default |
|---|---|---|---|---|
| 1 | Select one vendor | Enum of the three vendor labels | Always; exactly one vendor before a configured licence is complete | No vendor selected. |
| 2 | FPGA families for the selected vendor | Array of distinct family IDs | Only the selected vendor's family list; at least one valid family | No families selected. |
| 3 | Licence term and use | Enum of the three term options | Always after vendor selection; one permitted option | No term selected. |
| 4 | Select one band | Enum of the four band options | Only `rdp-yearly`; exactly one band | No band selected. |
| 5 | Fixed / node-locked licences | Boolean | Altera only; at least one of controls 5 and 6 enabled | Unchecked. |
| 6 | Floating licences | Boolean | Altera only; can be enabled alongside control 5 | Unchecked. |
| 7 | Number of fixed nodes | Positive integer while enabled | Only fixed mode; count must match complete host rows | Widget illustrates 1; canonical disabled count is 0. |
| 8 | Workstation reference — optional | Text, repeated per fixed node | Only fixed mode; optional for each row | Empty placeholder; not a literal workstation name. |
| 9 | NIC / host ID — required | Licence-manager-specific text, repeated per fixed node | Only fixed mode; required for every selected node | Empty placeholder; actual format unresolved. |
| 10 | Number of floating nodes / concurrent seats | Positive integer while enabled | Only floating mode | Widget illustrates 1; canonical disabled count is 0. |
| 11 | Licence server reference — optional | Text | Only floating mode; optional | Empty placeholder. |
| 12 | Licence server NIC / host ID — required | Licence-manager-specific text | Only floating mode; required for the drafted single-server arrangement | Empty placeholder; actual format unresolved. |
| 13 | Number of support packages | Nonnegative integer in the product configurator | Optional; purchases separate support SKU quantities | 0; calculated hours are quantity × 10. |

The actual field IDs are direct typed values, such as `vendor_id`, `family_ids`, `licence_term_id`, `production_band_id`, `fixed_enabled`, `fixed_node_count`, `fixed_hosts`, `floating_enabled` and `floating_seat_count`. A fixed-host row contains an optional `workstation_reference` and required `host_id`. The two per-row values explain why rendered field count increases with node count. The support selector creates or updates the separate support cart line; it does not alter the IP licence's host entitlement.

### Business checkout

The source provides **nineteen business/billing field groups**. Preserve the distinctions between explicitly required, optional, conditional and unspecified requiredness. Implement the country-specific address/tax profile after the relevant business rules are approved; the source does not provide a universal tax-status enum or require a postcode everywhere.

| # | Exact source field label | Source requirement | Proposed control / handling |
|---|---|---|---|
| 1 | Legal business / organisation name | Required | Text; identify the purchasing business. |
| 2 | Trading name | Optional | Text. |
| 3 | Business registration number | Where applicable; allow sole traders or entities without one | Text with a country/entity-specific applicability rule; no universal mandatory number. |
| 4 | Country of registration / establishment | Required | Country selector; its maintained option set requires a separate operational definition because the source supplies no list. |
| 5 | Registered business address | Required | Structured address whose relevant parts depend on country. |
| 6 | Billing address | Required; offer “Same as registered address” | Structured address plus the separate copy/link helper described below. |
| 7 | City, region and postcode | As applicable to the selected country | Country-specific address subfields; do not impose every component on every address. |
| 8 | VAT / tax identification number | Where applicable | Text; format and tax treatment are separate validations. |
| 9 | VAT / tax registration status | Required selection appropriate to customer location | Enum supplied by an approved tax profile; options are not specified in the source. |
| 10 | Purchasing contact name | Required | Text. |
| 11 | Business email address | Required | Email input. The source does not prescribe a domain allowlist. |
| 12 | Telephone number | Optional unless needed for fulfilment | Telephone input with conditional requiredness defined by a real fulfilment need. |
| 13 | Purchase order reference | Optional | Text. |
| 14 | Accounts / invoice email | Optional; defaults to purchasing contact | Email input; default from the purchasing contact email, visibly editable. |
| 15 | Technical / licence administrator name and email | Required; offer “Same as purchasing contact” | Name and email inputs, with the separate helper described below. |
| 16 | Licensed legal entity | Defaults to purchasing business; differences require review | Confirmed purchasing-entity reference by default; an explicitly different entity enters review. |
| 17 | Deployment / end-use country | Required for order review | Country selector; no inference from IP address, registration country or billing address. |
| 18 | Intended application | Short description; do not request confidential design details | Short text. The source does not explicitly mark this row required; proposed checkout enforcement should require a concise description for review, subject to SLL's approval. |
| 19 | Additional order notes | Optional | Text; advise against submitting unnecessary confidential material or secrets. |

Two additional convenience controls are specified: **“Same as registered address”** and **“Same as purchasing contact.”** Propose a clear linked state while a helper is selected: edits to the source values update the corresponding destination. Turning the helper off materializes the current values into independently editable fields. Record final values with the order; do not retain an unresolved “same as” pointer that could later change historical invoices or contacts.

The source does not specify character limits for these text fields. Choose proportionate technical limits as a documented implementation decision, show them to customers, and apply the same limits in the backend. Do not present an invented limit as a source requirement. Extra end-user/export details are requested only when the review actually requires them.

### Order declarations and marketing control

The source lists the following **four declarations before placing an order**, followed by **one separate, optional, initially unticked marketing control**. Preserve the wording during the initial draft import; legal review may later supply versioned replacements.

| # | Exact source wording | Proposed handling |
|---|---|---|
| 1 | I am purchasing for business or professional purposes and am authorised to place this order for the named organisation. | Require an explicit declaration before placement; record person and named organization. |
| 2 | I have read and accept the Terms and Conditions and the xSPI-MC IP Licence Agreement applicable to this configuration. | Require acceptance of the identified versions; record both document hashes and the applicable configuration/offer. |
| 3 | I have read and accept the Refund and Cancellation Policy. | Require acceptance of the identified policy version. |
| 4 | I confirm that the selected FPGA families, licence term, production band where applicable, node counts and submitted NIC / host IDs are correct. | Require confirmation of the current configuration revision and private host-data revision. |
| 5 | Send me SLL product news and offers by email. I can unsubscribe at any time. | Optional and unticked; independent of order eligibility and service processing. |

The draft groups declarations 1–4 under “Before Placing Your Order”; making all four mandatory is the proposed enforcement of that intended flow, not an observed running implementation. Show the privacy notice separately. Do not convert necessary order processing into marketing consent. Store the exact accepted statement/document versions, accepting identity, time and relevant order/configuration; a checkbox boolean alone is insufficient for a reviewable transaction record. [Source, section 8](#product-source-snapshot)


## Change and invalidation matrix (proposal reference)


| Customer change | Clear or recalculate | Preserve / next required action |
|---|---|---|
| Change vendor | Clear all selected families, selected term, production band, Altera mode settings, counts, workstation/server references and host IDs. Invalidate the priced IP offer and configuration confirmation. | Preserve unrelated business details and a separately selected support line. Require a valid term and families again. Show the effect of the change before applying it; do not restore hidden NIC data on a later switch back. |
| Change families within the same vendor | Re-evaluate coverage overlap, family charges, compatibility and offer eligibility. Invalidate the IP offer/configuration confirmation. | Retain access values only where the same approved manager/profile remains applicable; revalidate them. Unresolved overlap enters review. |
| Change term | Remove the prior production band and its adjustment. Re-evaluate permitted access rules, charge recurrence and the applicable agreement. Invalidate the offer and affected acceptances. | Retain same-vendor families. If the new term is RDP, require a fresh band; preserve host data only if still valid under the approved access profile. |
| Change RDP band | Reprice/reclassify the configuration. `higher-volume` becomes `requires_quote`; an unknown adjustment never becomes zero. | Preserve host counts and identifiers; production and development-access quantities remain independent. |
| Disable fixed mode | Set fixed count to zero; delete draft fixed-host rows/references; remove fixed-mode and fixed-node charges. | Preserve floating access. If neither mode remains, the Altera configuration is incomplete. |
| Enable fixed mode | Create count 1, following the source illustration, with a blank required host-ID row. | Validate this mode under the selected term; no additional unselected nodes are granted. |
| Increase fixed count | Append the required number of blank host rows with stable row IDs; recalculate charges. | Preserve existing valid rows. Every new required identifier must be supplied before fulfilment eligibility. |
| Reduce fixed count | Identify the rows being removed, let the customer choose/cancel before applying the reduction, then delete those draft values and recalculate charges. | Preserve the remaining row identities. Do not silently renumber one host into another entitlement. |
| Disable floating mode | Set floating count to zero; delete draft server reference/host ID; remove floating-mode and floating-node charges. | Preserve fixed access. Require at least one active mode. |
| Enable floating mode | Create seat count 1, following the source illustration, with a blank required server host ID. | Do not request one host ID per floating seat. |
| Change floating seat count | Recalculate seats and charges; invalidate the offer/configuration confirmation. | Retain the same valid server identity if the approved manager supports the new count. |
| Edit a NIC / host ID | Validate and normalize under the actual manager; rerun duplicate checks; invalidate the host-data confirmation and offer configuration digest. | Unchanged counts need not invent a new surcharge. A host change to a purchased licence is a rehosting workflow, not an edit of the original order. |
| Change purchasing entity, licensed entity or billing/tax facts | Recalculate tax/review status and invalidate the relevant order/contract acceptance. A different licensee requires review. | Preserve technical configuration unless the approved licence rules make it entity-specific. |
| Change support-package quantity | Update the independent support line and current payable total. | Preserve IP term, production band and node entitlements. Do not multiply support when another IP line is added. |

Any material change after transaction review requires a fresh review of the affected quote/configuration and current transaction declarations. Preserve optional marketing preference independently. An accepted, unexpired sales offer has its own immutable terms and expiry: do not overwrite it by mutating a catalog record. If the customer edits its configuration, create a new offer revision.
