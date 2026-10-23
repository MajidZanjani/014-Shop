# Protected-offer pre-execution critique

Reviewed f2bcd66 against COM-02–06/DATA-01–04, the embedded product and P register, actual offer_preparation, preparation_snapshots, access/catalog models, document_preview, request_envelope/envelope_capture and constrained local archive records. Inline source critique, not independent review, commercial/legal approval or runtime qualification.

**Result:** design corrected; full offer-domain implementation is not ready. No independently useful new blocked-candidate runtime was identified: the existing PreparationAssessment already retains that capability. Do not add a parallel store/approval source simply to make an unfinished offer model appear implemented.

## Corrected design findings

| ID | Demonstrated issue | Correction |
|---|---|---|
| D-01 | The design called its prose field groups a closed field contract, but supplied no literal key sets/types/bounds/schema identity or approved-reference interface. The actual request validator is closed and bounded; it cannot serve as an offer validator by renaming its kind. | Rename the section to a proposed field inventory and explicitly retain executable-schema work as pending. Future exact encoding/reference limits must be tested against actual host/approval/text interfaces; no131072-byte inheritance or fabricated policy values. |
| D-02 | A distinct publication identity/time recorded before exposure could be read as proof that the customer had received the offer. That conflicts with prepared-versus-actual evidence and uncertain-response handling. | Archive the intended issued snapshot first; separately define the actual visibility/issue transaction and externally observed delivery facts. A prepared timestamp or lost response proves neither completed delivery nor its absence. No publication runtime is authorized by the wording correction. |

The identity direction is also explicit: immutable candidate first, then decision referencing its hash, then distinct later operation facts. Candidate bytes never contain a future decision/acceptance digest or acquire a circular content dependency.

## Remaining implementation gates

| Boundary | What source inspection establishes | What remains missing |
|---|---|---|
| Exact schema/recoverability | request_envelope validates a current-source131072-byte request-only shape; local captured source/intent checks are implemented. | Literal offer key/type/range/byte contract, approved content reference validation and custody/recovery interfaces. No domain schema is inferred. |
| Per-line applicability | Actual cart retains separate quantity-one IP lines and positive support quantity. Document preview distinguishes IP/support/mixed. assess returns blocked and pending values. | Exact approved per-line rate/rights/access/coverage/tax/text revisions and applicable non-applicability decisions. Support-only omits IP host prerequisites but still lacks its own required inputs. |
| Approval authority | StaffQuotationGrant grants reviewer assignment and one positive exact business scope. PreparationAssessment captures internal actor/MFA and disabled assessments. | Protected commercial approver role/resource assignment, reset/recovery/freshness semantics and exact approved-source references. No reviewer-is-approver alias or invented second approver. |
| Scope/lock order | Existing preparation writes lock credential then quotation; request capture/status additionally lock cart and retained fact/intent. Current grants serialize through supported local operator credential/quotation locks. | Actual host/source-approval/domain services and a compatible aggregate lock graph. A proposed total order without those interfaces would claim an integration that does not exist. |
| Clocks | Source and COM-06 require separate quote validity, order payment-start and bank-session expiry. Actual preparation only projects null advisory fields. | Approved policies and start anchors, strict timezone/precision/validity boundary rules and per-operation deadline materialization. A bank session does not exist at candidate formation and cannot be required to supply a fictitious expiry then. |
| Actual domain effects | Current archive models constrain retention/effects to false; selected local readback is prepared evidence only. No OfferRevision/Acceptance/Order model exists. | Distinct protected decision/publication/acceptance schemas, atomic visibility/order conversion, qualified archive and uncertain-result reconciliation. A successful prepared readback cannot create these facts. |

## Reuse decision and scoped continuation

PreparationAssessment already provides immutable-by-API versioned blocked assessments, expected revision/displayed digest checks, retry arbitration, original attribution, retained reads and current/retained comparisons. Its missing commercial values are intentional and its flags are unconditionally false. A new blocked-candidate model or serializer over the same data would add another vocabulary without satisfying any missing input. Reuse this existing boundary for further actual local defects; do not manufacture an offer/domain completion.

Current full07-02 runtime work is held only at the affected approval/schema/host/entity/tax/text/retention boundaries listed in the design and single P register. Request capture/status and unrelated ready local portions retain their existing authorization. Country/tax answers are user-deferred; do not repeatedly ask. No independent runner is assigned; no provision/purchase/collector expansion. This critique does not require another generic permission confirmation.

Next useful continuation is a bounded source audit of the existing preparation/review/document read boundaries for demonstrated cross-scope, stale-revision or private-output defects, reusing their actual interfaces. Fix only a reproduced local defect; avoid adding another candidate/approval subsystem or synthetic approvals. Full human/source/transport/off-host/provider/recovery/production acceptance remains pending.

## Verification scope

Design/source/link checks only. No runtime/test/migration/product-source changes. Retain b96b665's275 local tests/observations (261 Django plus14 Gunicorn),5 checks,71.878s and exact source163 files21 templates/no symlinks; unchanged code is not rerun. Neither this critique nor the prior passing tests close full07-02 or07-03.
