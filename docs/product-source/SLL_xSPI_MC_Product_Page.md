# SLL xSPI-MC IP — Configure Your Licence

> Working draft: product-page copy, form specification and commercial rules. Values in square brackets require completion. Controls shown here are illustrative; this Markdown file does not implement a working cart. Proposed assumptions and unresolved decisions are listed at the end.

Configure your xSPI-MC IP licence for your FPGA platform, development team and production requirements.

**Included:** encrypted RTL, user manual, reference design and licence key for the purchased configuration.

**[ Configure Your Licence ]**

## 1. Select Your FPGA Vendor and Families

Choose **one FPGA vendor** per configured licence, then select **one or more FPGA families** from that vendor.

| Select one vendor | Base licence price |
| --- | --- |
| ( ) Altera / Intel FPGA | From €[ALTERA_BASE_PRICE] |
| ( ) AMD / Xilinx | From €[AMD_BASE_PRICE] |
| ( ) Microchip | From €[MICROCHIP_BASE_PRICE] |

Prices exclude applicable VAT. The final price depends on the selected licence term, FPGA families, production band where applicable, and node configuration.

The base price includes one selected FPGA family. Each additional family from the same vendor adds **€[ADDITIONAL_FAMILY_PRICE]**.

### Altera / Intel FPGA

Show these options only when Altera / Intel FPGA is selected:

- [ ] Cyclone 10 LP (C10LP)
- [ ] MAX 10
- [ ] Cyclone 10
- [ ] Cyclone 10 GX
- [ ] Cyclone V
- [ ] Stratix 10
- [ ] Agilex 3
- [ ] Agilex 5

### AMD / Xilinx

Show these options only when AMD / Xilinx is selected:

- [ ] Series 7
- [ ] UltraScale
- [ ] UltraScale+

### Microchip

Show these options only when Microchip is selected:

- [ ] PolarFire
- [ ] PolarFire SoC

**Selected families:** [FAMILY_LIST]  
**Additional-family charge:** €[FAMILY_CHARGE]

For another vendor, add a separately configured licence to your cart.

## 2. Select Your Licence Term and Use

Select one option:

| Option | Availability | Description |
| --- | --- | --- |
| ( ) R&D — annual | All listed vendors | Annual research and development licence. Production rights are not included unless expressly granted in the licence agreement. |
| ( ) RDP — yearly | Altera / Intel FPGA only | Annual licence covering research, development and production within the purchased production band, subject to the licence agreement. |
| ( ) Perpetual | All listed vendors | Non-expiring licensed rights as defined in the licence agreement. Maintenance, updates and support entitlements are stated separately. |

**Licence price for your selection:** €[LICENCE_PRICE] [per year / one-time]

The licence agreement and order confirmation identify the permitted use, covered families, licence start date, duration and applicable restrictions.

<!-- Confirm the RDP expansion and precise permitted-use definitions before publication. Do not assume perpetual automatically means unlimited production, updates or support. Display the final perpetual production rights and annual renewal/expiry behaviour here before checkout is enabled. -->

## 3. Select Your Production Volume

**Show this section only for RDP — yearly.**

Choose the production band required for your licence period:

| Select one band | Production units | Price adjustment |
| --- | --- | --- |
| ( ) Band 1 | 1–100 | €[BAND_1_ADJUSTMENT] |
| ( ) Band 2 | 101–1,000 | €[BAND_2_ADJUSTMENT] |
| ( ) Band 3 | 1,001–5,000 | €[BAND_3_ADJUSTMENT] |
| ( ) Higher volume | More than 5,000 | Request a quotation |

Select a band that covers your expected production. Contact SLL before exceeding the licensed limit.

**Production counting rule:** [DEFINE WHAT COUNTS AS ONE UNIT]  
**Measurement period:** [DEFINE LICENCE YEAR OR OTHER AGREED PERIOD]  
**Aggregation:** [DEFINE WHETHER UNITS ARE COMBINED ACROSS PRODUCTS, PROJECTS AND SELECTED FAMILIES]

<!-- Proposed: measure volume per annual licence period. Confirm this, the upgrade process, reporting obligations and production rights after expiry before launch. The bands intentionally avoid overlap at 1,000. Higher-volume selections use Request a Quotation instead of checkout with an unknown price. -->

## 4. Configure Licence Access

**Show this section only for Altera / Intel FPGA.**

Choose fixed nodes, floating nodes, or both. Node counts relate to development licence access and are separate from production volume.

- [ ] Fixed / node-locked licences
- [ ] Floating licences

### Fixed / Node-Locked Licences

**Number of fixed nodes:** [ − ] [1] [ + ]

Provide the NIC / host ID required for each licensed workstation.

| Fixed node | Workstation reference — optional | NIC / host ID — required |
| --- | --- | --- |
| 1 | [WORKSTATION_NAME] | [NIC_ID] |
| 2…N | [WORKSTATION_NAME] | [NIC_ID] |

One row appears for each fixed node selected. Enter the identifier for the workstation on which the licence will be used.

**Fixed-node surcharge:** €[FIXED_NODE_SURCHARGE]

### Floating Licences

**Number of floating nodes / concurrent seats:** [ − ] [1] [ + ]

**Licence server reference — optional:** [SERVER_NAME]  
**Licence server NIC / host ID — required:** [SERVER_NIC_ID]

Proposed configuration: the licence is bound to the licence server, with the selected number of concurrent seats. Do not enter a separate client workstation NIC ID for every floating seat.

<!-- Confirm the actual licence manager's host-ID format, server requirements, redundancy support and concurrent-seat semantics. If several servers are permitted, provide separate server rows with seat allocations whose sum equals the purchased floating seat count. -->

**Floating-node surcharge:** €[FLOATING_NODE_SURCHARGE]

### Additional-Node Pricing

Proposed rule based on the requested threshold:

- No extra-node surcharge for the first five fixed nodes.
- No extra-node surcharge for the first five floating nodes.
- Each fixed node above five adds **€50**.
- Each floating node above five adds **€50**.
- Fixed and floating nodes may be selected together.

| Fixed nodes | Floating nodes | Extra chargeable nodes | Extra-node charge |
| --- | --- | --- | --- |
| 5 | 0 | 0 | €0 |
| 6 | 0 | 1 | €50 |
| 3 | 3 | 0 | €0 |
| 5 | 5 | 0 | €0 |
| 7 | 6 | 3 | €150 |

The €50 rate is illustrative pending confirmation. Any separate charge for enabling fixed or floating access must be shown in the order summary.

<!-- The table assumes separate five-node allowances, not five combined seats. It does not grant unselected nodes. Confirm whether the allowance really permits five fixed plus five floating without an additional mode charge. Also confirm whether node surcharges recur annually or apply only once. -->

For AMD / Xilinx and Microchip, display the applicable licence-access conditions in the licence summary. Do not collect NIC IDs unless they are required by the actual licensing mechanism.

## 5. What You Will Receive

Your purchase includes:

- **Encrypted RTL** for the purchased xSPI-MC configuration and FPGA families.
- **User manual** covering the supplied IP.
- **Reference design** for the supported configuration identified in your order.
- **Licence key** matching the purchased entitlement and host configuration where applicable.

**Delivery method:** [SECURE DOWNLOAD / CUSTOMER PORTAL / EMAIL]  
**Expected delivery:** [DELIVERY TIMESCALE AFTER ORDER ACCEPTANCE AND REQUIRED DETAILS]

The purchase grants the rights specified in the licence agreement; it does not transfer ownership of SLL intellectual property or provide unencrypted RTL.

**Supported tool versions and reference-design targets:** [COMPATIBILITY_DETAILS]

## 6. Optional Engineering Support

Need help integrating or troubleshooting xSPI-MC?

**10-Hour FPGA IP Technical Support Package — €[SUPPORT_PRICE] + applicable VAT**

**Number of support packages:** [ − ] [0] [ + ]  
**Total support hours:** [QUANTITY × 10]

- Purchased support hours do not expire.
- Additional packages may be purchased later.
- After each performed support task, an email records hours used for that task, total hours used to date and the remaining balance.

**[ View Support Package Details ]**

IP maintenance, updates and any included support are governed by the selected licence terms. Separately purchased engineering support does not extend an annual IP licence.

## 7. Your Configuration and Price

Keep this summary visible as the customer makes selections.

| Item | Selection / amount |
| --- | --- |
| FPGA vendor | [VENDOR] |
| FPGA families | [FAMILY_LIST] |
| Licence term and use | [R&D ANNUAL / RDP YEARLY / PERPETUAL] |
| Production band — RDP only | [BAND AND PERIOD] |
| Fixed nodes — Altera only | [COUNT] |
| Floating seats — Altera only | [COUNT] |
| Base licence, including one family | €[BASE_PRICE] |
| Additional FPGA families | €[FAMILY_CHARGE] |
| Production-band adjustment — RDP only | €[VOLUME_CHARGE] |
| Licence-access mode charges, if applicable | €[MODE_CHARGE] |
| Additional fixed nodes | €[FIXED_NODE_CHARGE] |
| Additional floating seats | €[FLOATING_NODE_CHARGE] |
| Optional engineering support | €[SUPPORT_CHARGE] |
| Subtotal excluding VAT | €[SUBTOTAL] |
| VAT | [CALCULATED AT CHECKOUT] |
| Total payable | €[TOTAL] |

**Annual licence details:** [START DATE, END DATE, RENEWAL METHOD AND RENEWAL PRICE/BASIS]  
**Perpetual licence details:** [PERMITTED USE AND MAINTENANCE/UPDATE ENTITLEMENT]

**[ ADD CONFIGURED LICENCE TO CART ]**

NIC IDs should be masked in the ordinary cart summary, with an authenticated edit option.

## 8. Business Checkout

### Business and Billing Details

| Field | Requirement |
| --- | --- |
| Legal business / organisation name | Required |
| Trading name | Optional |
| Business registration number | Where applicable; allow sole traders or entities without one |
| Country of registration / establishment | Required |
| Registered business address | Required |
| Billing address | Required; offer “Same as registered address” |
| City, region and postcode | As applicable to the selected country |
| VAT / tax identification number | Where applicable |
| VAT / tax registration status | Required selection appropriate to customer location |
| Purchasing contact name | Required |
| Business email address | Required |
| Telephone number | Optional unless needed for fulfilment |
| Purchase order reference | Optional |
| Accounts / invoice email | Optional; defaults to purchasing contact |
| Technical / licence administrator name and email | Required; offer “Same as purchasing contact” |
| Licensed legal entity | Defaults to purchasing business; differences require review |
| Deployment / end-use country | Required for order review |
| Intended application | Short description; do not request confidential design details |
| Additional order notes | Optional |

Collect further end-user or export information only where needed for review. Do not request identity documents or sensitive technical material through a general notes field.

### Before Placing Your Order

- [ ] **I am purchasing for business or professional purposes and am authorised to place this order for the named organisation.**
- [ ] **I have read and accept the Terms and Conditions and the xSPI-MC IP Licence Agreement applicable to this configuration.**
- [ ] **I have read and accept the Refund and Cancellation Policy.**
- [ ] **I confirm that the selected FPGA families, licence term, production band where applicable, node counts and submitted NIC / host IDs are correct.**

**Privacy notice:** We process business contact, billing and licence-identification data to administer your order, issue and manage licences, communicate with you and meet applicable obligations. See our **[Privacy Policy]** for details.

Optional, unticked:

- [ ] **Send me SLL product news and offers by email. I can unsubscribe at any time.**

**Order total, including applicable taxes:** €[TOTAL]  
**[ PLACE ORDER AND PAY €TOTAL ]**

<!-- Do not make marketing consent a purchase condition. Do not use “I consent to GDPR” or bundle mandatory service processing into marketing consent. Link policies and show their versions before acceptance. If the store uses invoice or quotation workflows instead, adapt the final button and state when payment and acceptance occur. -->

## Frequently Asked Questions

### Can I select more than one FPGA vendor?

Each configured licence covers one vendor. You may select multiple families from that vendor. Add another configured licence to the cart for another vendor.

### How are additional FPGA families charged?

The base licence includes one selected family. Each additional family from the same vendor adds the displayed family charge.

### Which licence options are available?

R&D annual and perpetual licences are available for all listed vendors. Yearly RDP is available only for Altera / Intel FPGA.

### When do I select a production band?

A production band is required for yearly RDP. Other licence options have the production rights explicitly stated in their licence agreement.

### Can I combine fixed and floating licences?

Yes, for Altera / Intel FPGA. Select both access options and enter the required node counts and host information.

### Do development nodes count as production units?

No. Development nodes or floating seats define access to the development licence. Production volume defines the number of units covered by the production entitlement.

### Which NIC ID should I enter?

For fixed licences, provide the required NIC / host ID for each licensed workstation. For floating licences, provide the required licence-server ID. Follow the licensing instructions linked beside the field.

### What happens if I replace a workstation or licence server?

Contact SLL before changing the licensed host. Rehosting eligibility, charges and procedure are governed by the licence agreement.

### Does perpetual include unlimited support or updates?

Only the maintenance, update and support entitlements expressly included in your order apply. Engineering support may be purchased separately in non-expiring 10-hour bundles.

### What happens when an annual licence expires?

[INSERT APPROVED RULES FOR DEVELOPMENT ACCESS, RENEWAL, NEW PRODUCTION AND ALREADY DEPLOYED PRODUCTS.] These terms must be visible before purchase.

## Commercial and Legal Information

### Licence Scope and Intellectual Property

The order confirmation and applicable xSPI-MC licence agreement identify the licensed entity, vendor, FPGA families, permitted use, term, production entitlement and node allocation.

SLL retains ownership of its IP, RTL, documentation, reference designs and other supplied materials. Use and distribution are permitted only within the rights granted by the licence agreement. Customer materials remain the property of their respective owners.

### Order Acceptance and Delivery

An automated order acknowledgement confirms receipt of an order. Final acceptance and fulfilment follow the process stated in the Terms and Conditions, including payment, configuration and any necessary compliance checks.

Before purchase, state the delivery timescale, delivery method, cancellation/refund terms and how payments are returned if an order is declined.

### Annual and Perpetual Terms

Annual duration, start date, renewal method, renewal pricing and expiry consequences must be specified in the order and licence agreement. Do not enable automatic renewal unless its terms and customer authorisation have been established.

A perpetual licence grants the non-expiring rights stated in its agreement. It does not automatically grant unrestricted production, future versions or continuing engineering support.

### Taxes and Invoices

Product prices are displayed excluding VAT, with applicable tax and the total payable shown before the order is placed. Tax treatment depends on the supplier, customer location and status, and the applicable rules. Supplying a VAT number does not by itself guarantee a VAT exemption or reverse-charge treatment.

An invoice is issued using the confirmed legal entity and billing information.

### Privacy and Licence Identifiers

[SLL LEGAL ENTITY] uses order, business-contact and host-identification information for order administration, invoicing, licence generation and management, support, security and applicable legal obligations.

NIC / host IDs may identify or be linked to a person or workstation. Restrict their use to the documented licensing and security purposes, limit access, and retain them according to the published retention policy.

The Privacy Policy must identify the controller and contact details, processing purposes and legal bases, recipients, retention periods or criteria, relevant international transfers and safeguards, applicable rights and complaint routes. Explain required fields and the consequences of not providing them.

Choose the actual legal basis for each processing purpose. Where a company is the contracting customer, do not automatically assume that every employee's data is processed under a contract with that individual. Optional marketing consent is separate from processing needed to administer the business relationship.

### Confidentiality

Technical materials submitted for compatibility checks or support are handled under the applicable confidentiality terms and any NDA in force. Customers should submit only necessary information and must not enter passwords, private keys or unrelated personal information into the form.

### Customer Responsibilities

The customer remains responsible for its final design, verification, validation, implementation, production testing and applicable safety and regulatory requirements. Product-specific specifications, warranties, remedies and liability provisions are set out in the licence agreement and Terms and Conditions.

### Export Controls and Sanctions

SLL and the customer must comply with applicable export-control and sanctions obligations. SLL may request relevant end-use information or decline or suspend fulfilment where required by applicable law. Customer declarations do not replace SLL's own compliance obligations.

### Seller Information and Policy Links

Display the actual contracting supplier's:

- Legal name, registered address and contact email.
- Company registration and VAT numbers where applicable.
- Terms and Conditions.
- xSPI-MC IP Licence Agreement.
- Privacy Policy and privacy contact.
- Refund and Cancellation Policy.
- Cookie information and controls appropriate to the website's actual technologies.

Do not assume the seller's jurisdiction from the customer's or consultant's location.

---

## Implementation Notes — Not Customer-Facing Copy

### Selection and Validation Rules

1. Require exactly one vendor and at least one valid family from that vendor.
2. Use distinct family identifiers. Confirm whether “Cyclone 10” is a separate licensed option or an umbrella for LP/GX; prevent duplicate charging for overlapping coverage.
3. On a vendor change, clear incompatible families, node settings and NIC IDs, and require a valid licence option again. Preserve unrelated business details.
4. Offer yearly RDP only for Altera. Require exactly one volume band only while RDP is selected. Clear its price adjustment when another term is selected.
5. For Altera, require at least one enabled access mode. Enabled modes require a positive integer count; disabled modes have zero count and zero charge.
6. Fixed-node count must match the number of complete host-ID rows. Floating seat count must be a positive integer, with the required server identification.
7. Validate and normalise host IDs against the actual licence manager's documented format; do not assume every accepted host identifier is a 12-digit MAC address. Detect unintended duplicate fixed-host entries.
8. For non-Altera vendors, omit Altera node surcharges and host fields. Configure their actual access rules before those options can be sold.
9. Recalculate on every relevant change. Enforce the same eligibility, price and validation rules on the server before checkout and fulfilment.
10. Never treat a missing price as zero. Use “Request a Quotation” or block payment when the configuration lacks approved pricing or terms.
11. Keep each differently configured licence as a separate cart line. Do not multiply host entitlements through an ambiguous generic quantity box.
12. Version the price rules and licence terms. Store the purchased configuration, acceptance records and price breakdown with the order.
13. Use the payment provider's secure checkout. Confirm payment server-side and make fulfilment idempotent so retries cannot issue duplicate entitlements.
14. Treat licence keys and host identifiers as restricted order data; keep them out of URLs, analytics events and public logs.

### Proposed Price Calculation

Let:

- B = base price for the selected vendor and licence term, including one family.
- F = number of selected, distinct licensed families.
- A = additional-family price for that vendor and term.
- V = selected production-band adjustment, zero outside yearly RDP.
- M = explicitly configured access-mode charges, zero if none.
- Nf = fixed-node count; Nl = floating-seat count.
- E = extra-node rate, provisionally €50.
- Q = optional support-package quantity; S = price per 10-hour package.

Then:

```text
family_charge = max(F - 1, 0) × A
fixed_extra   = max(Nf - 5, 0) × E
floating_extra = max(Nl - 5, 0) × E

ip_subtotal = B + family_charge + V + M + fixed_extra + floating_extra
support_subtotal = Q × S
subtotal = ip_subtotal + support_subtotal
total_payable = subtotal + applicable_tax
```

For AMD / Xilinx and Microchip, Nf and Nl are zero in this formula unless separate rules are approved. This draft applies the node allowance once per configured licence, not once per FPGA family.

Display annual and one-time components separately. Support is purchased separately and must not be silently added to annual renewals. Confirm recurrence of family, volume, mode and node charges before implementing renewals.

### Commercial Decisions Required Before Launch

| Decision | Draft treatment / action |
| --- | --- |
| Base and additional-family prices | Placeholders; confirm by vendor and term |
| Family allowance | Assumes one family in the base price |
| Cyclone 10 overlap | Preserve requested options; confirm distinct coverage before charging |
| RDP production bands | 1–100, 101–1,000, 1,001–5,000; quote above 5,000 |
| Production accounting | Define unit, aggregation, period, reporting and upgrades |
| Perpetual production rights | Unresolved; do not silently treat as unlimited |
| Annual renewal / expiry | Define renewal and effects on development and production |
| Five-node allowance | Assumes five fixed plus five floating independently |
| Extra-node rate | €50 illustrative; confirm recurring versus one-time |
| Fixed/floating base charges | Unresolved; show separately if applicable |
| Floating licensing | Assumes concurrent seats bound to a server; verify mechanism |
| Non-Altera access | Define actual key, host and seat requirements |
| Rehosting | Define entitlement, procedure and charges |
| Updates, maintenance and warranty | Define inclusions, duration and remedies |
| Delivery | Define method, compatibility coverage and timeframe |
| Contracting supplier and policies | Insert verified entity details and final policy links |

The draft becomes publishable once these commercial terms and supplier-specific legal/privacy information are completed and reviewed.

### Privacy Drafting References

- [Irish Data Protection Commission — Guidance on legal bases for processing personal data](https://www.dataprotection.ie/en/dpc-guidance/guidance-legal-bases-processing-personal-data)
- [CNIL — Inform users](https://www.cnil.fr/fr/node/681)

These references inform the privacy structure; they do not certify this form or website as GDPR-compliant.

