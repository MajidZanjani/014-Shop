# Scoped SHB coupon preview and request reservations

Authority: [SHB revision 1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). This is a verified local slice of07-02; full plan/phase/payment acceptance is pending.

The protected common form now supports Apply/Remove without JavaScript. A code changes the authoritative integer-money estimate, never purchased hours. FPGA previews remain subject to the existing eligibility and disabled-checkout boundary. ASIC submission atomically retains the discount policy and one slot with the existing quotation/request snapshot. Apply and GET create no reservation. Concurrent invitations for the same customer cannot claim the same remaining use.

Only a digest of a normalized random code is stored. Codes use a keyed SHA256 verifier; raw codes are excluded from request details, snapshots and database records. The ten-attempt/ten-minute customer budget spans invitations and commits independently of rejected or interrupted captures. A committed request retry returns its original amount/policy before consulting today's rate or coupon status, without spending another guessing attempt. Different details/code/quantity under that request identity fail closed. Database triggers preserve policy, monotonic revocation and held-reservation identity, validate customer/variant/policy/capacity and forbid an unsafe release or consumption.

Issuance is explicitly fake-only, with a named synthetic policy, synthetic percentage/rate/tax values and no real approval. The example30-day claim window is a fixture, not commercial adoption. Reservation consumption/release, FPGA payable orders, assigned ASIC offers, transaction notifications and financial finalization remain pending. No reservation is automatically freed by a clock or revocation; no payment, support-time credit/debit, customer balance or task email is created.

| Executed observation | Result | Scope |
|---|---|---|
| Test-first baseline | Existing20 SHB tests passed; all12 initial coupon tests failed with the absent discount module | Expected red baseline, before implementation |
| Focused and shared PostgreSQL18.6 lane | `SHB_LOCAL_PASS checks=7 tests=250 shared_tests=205 duration_seconds=84.536` |9 source/private-release,20 existing SHB,16 coupon,95 access/recovery,104 payment,6 truly network-isolated adapter tests. None failed/skipped. |
| Direct SQL race without the application's access-epoch lock | One insert held the slot; the other returned PostgreSQL uniqueness SQLSTATE23505 | Separate connections/transactions; invalid extra slot and forged policy also rejected |
| Real Chromium155.0.8059.84 / browser Node24.21.0 | `SHB_BROWSER_PASS checks=33 modes=2` | JavaScript/no-JavaScript,320px, native keyboard Apply/Remove, ASIC50-hour/EUR9,000 discounted request and FPGA30-hour/EUR3,000 review; two held reservations, zero payments/fulfilments |
| Usable loopback/header demonstration | `SHB_DEMO_PASS checks=17` | Private fixture capture, authoritative preview, repeated discounted request, old-route/access denial; fake-only |
| Exact inert packaged backend source | `SHB_SOURCE_PASS checks=2 files=300 imported_modules=10 duration_seconds=3.498` | [Exact hashes](../evidence/shb/source-revisions/1631617322cdee45c1a6f1c330b41e8dcfed367fa31b1cc8dc57075829d09b1a.json); source-only, no runtime activation |

The browser used the unchanged private9-file Astro snapshot `.scratch/shb-private-resume-t2p3r5cc/release`, manifest `ef2d68408ac264a2da888af45ec167242c1a21680990d66a772bd761b86941f3`. New form behavior is rendered by the protected Django route. Frontend source/pins were unchanged; the previously passing build is retained. No credentials/.env, actual bank/mail/object storage, protected host/service/DNS/TLS action or paid provisioning was used. `http_cache.sqlite` remains untouched.

Reproduce from the repository root:

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb.py --shared
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#browser --command python3 scripts/demo_shb.py --check --browser --release .scratch/shb-private-resume-t2p3r5cc/release
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/demo_shb.py --check --release .scratch/shb-private-resume-t2p3r5cc/release
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb_source.py
python3 scripts/check_planning.py
python3 scripts/check_purchase_plan.py
```

For an interactive demonstration, use the browser-shell command above with `--serve --release .scratch/shb-private-resume-t2p3r5cc/release` instead of `--check --browser --release ...`. Open the invitation and optional synthetic10% code from the two private files whose paths it prints. Use Synthetic Company Limited and a synthetic.invalid contact. The demo code deliberately permits two uses for the two-mode browser exercise; the normal issuance fixture defaults to one. Ctrl-C closes only the owned demo/database contexts. Never publicly serve the release directory.

Locking/transaction semantics follow the pinned Django5.2 documentation: [transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) and [select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update). Actual company/commercial/provider and independent runtime/recovery/host/ingress qualifications remain in the single register `docs/decisions.md`; no local observation adopts or satisfies them.
