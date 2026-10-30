# Supporting Hours Bundle — local partial demonstration

Current authority: [SHB revision1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). Current implementation and next action: [STATE](../.planning/STATE.md) / [ROADMAP](../.planning/ROADMAP.md). Exact implemented behavior, executed checks, failures and all commands: [bootstrap report](build/shb-bootstrap-2026-10-30.md) and [repaired local verification](build/shb-resume-2026-10-30.md).

The current loopback demo supports the shared minimum form, FPGA price review and once-only synthetic ASIC request capture. FPGA Checkout is disabled. Paid FPGA orders, reviewed ASIC offers, discounts and transaction notifications remain unfinished. Support usage and task emails stay manual outside the shop; no online balance, grant or support panel is created.

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/demo_shb.py --serve
```

Open the invitation URL from the private file named by the command. Use the fictional company `Synthetic Company Limited` and a `.invalid` contact. Ctrl-C stops only this owned demo and its disposable database. No server remains running after verification. The retained private Astro snapshot can be selected with `--release .scratch/shb-private-resume-t2p3r5cc/release`; never serve that directory publicly.

Shared234 tests (including six actually network-isolated adapter tests), actual Chromium27 checks/two modes, fresh exact frontend build/check/default tests and295-file/eight-import source verification pass. Paid workflows and actual commercial/provider/deployment qualification remain pending in [decisions.md](decisions.md). No real payments, emails or external operations are enabled.
