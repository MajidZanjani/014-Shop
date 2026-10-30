# Supporting Hours Bundle — local partial demonstration

Current authority: [SHB revision1.1](../014-Shop-SHB-Proposal-Revision-2026-10-30.md). Current pause and next action: [STATE](../.planning/STATE.md) / [ROADMAP](../.planning/ROADMAP.md). Exact implemented behavior, executed checks, failures and all commands: [SHB batch report](build/shb-bootstrap-2026-10-30.md).

The current loopback demo supports the shared minimum form, FPGA price review and once-only synthetic ASIC request capture. FPGA Checkout is disabled. Paid FPGA orders, reviewed ASIC offers, discounts and transaction notifications remain unfinished. Support usage and task emails stay manual outside the shop; no online balance, grant or support panel is created.

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/demo_shb.py --serve
```

Open the invitation URL from the private file named by the command. Use the fictional company `Synthetic Company Limited` and a `.invalid` contact. Ctrl-C stops only this owned demo and its disposable database. No server remains running at the pause. The retained private Astro snapshot can be selected with `--release .scratch/shb-private-release-t89j52jy/release`; never serve that directory publicly.

Focused29 tests, full frontend138 tests, loopback16 checks and the corrected95-case shared security/recovery group pass for their stated scope. Actual Chromium startup fails and the next110 shared cases include six adapter-harness guard failures; aggregate verification remains incomplete. Live commercial/provider/deployment inputs stay pending in [decisions.md](decisions.md). No real payments, emails or external operations are enabled.
