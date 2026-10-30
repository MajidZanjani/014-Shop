# SHB local verification repaired — 30 October 2026

Authority: [SHB revision1.1](../../014-Shop-SHB-Proposal-Revision-2026-10-30.md). Current STATE/ROADMAP route to07-02. The [bootstrap report](shb-bootstrap-2026-10-30.md) retains the earlier pause and failures; the observations below supersede those two open local verification issues. No full SHB release/parent-plan acceptance is claimed.

The owned startup log showed Chromium's Unix SingletonSocket path exceeded the108-byte system limit under the nested workspace TMPDIR. `scripts/demo_shb.py` now supplies a short private per-run/tmp directory and cleans it through its own context. After startup, a value-free diagnostic established zero native POSTs: the harness's Enter event omitted its character event. `scripts/browser_shb.mjs` now uses the existing `browser_purchase.mjs` carriage-return dispatch pattern. Optional failure evidence contains only stage, response status, POST count, field names and a CSRF-denial boolean; no token, URL or field value. Two missing word spaces in the storefront copy were also fixed from actual screenshots.

`scripts/check_shb.py --shared` now calls the existing `check_backend.qualify_adapters()` lane, which really executes `unshare --net` before setting its guard in the child. All original adapters and shared assertions remain. The lane returns its observed test count for aggregation.

| Executed observation | Actual result | Limit |
|---|---|---|
| Focused plus shared runner on disposable PostgreSQL18.6 | `SHB_LOCAL_PASS checks=7 tests=234 shared_tests=205 duration_seconds=81.428` | Nine source/private-release controls,20 SHB,95 access/recovery,104 payment,6 truly network-isolated adapters; no failed/skipped cases. Local/synthetic. |
| Real Chromium155.0.8059.84, browser Node24.21.0 | `SHB_BROWSER_PASS checks=27 modes=2` | JavaScript hydration and no-JavaScript,320px layout, keyboard/native protected POST, ASIC50-hour request and FPGA30-hour/EUR3,000 fixture review, no browser-storage persistence or external request; two requests retained and zero payment/fulfilment. Full paid flow/formal accessibility/human review remains pending. |
| Fresh exact frontend Node24.22.0/npm11.19.1 | `PUBLIC_BROWSER_BUILD_PASS` from reused build helper; check/build/full default npm tests all execute successfully | The helper name does not mean public publication. Same full default suite retained; no dependency pin change. |
| Private release |9 files; manifest `ef2d68408ac264a2da888af45ec167242c1a21680990d66a772bd761b86941f3` | `.scratch/shb-private-resume-t2p3r5cc/release`; only through the protected Django route. Final27-check browser pass used this exact snapshot. |
| Refreshed exact inert backend source |295 files,8 isolated imports,2 checks,3.490s | `/nix/store/6xxs4lrppnp5lww8s05w72q9sb207xg5-shop-python-source`; [record](../evidence/shb/source-revisions/c8c09f5e9f46deb03efea8eb55abc358da0523a4f7e68769206f8784a9e968c0.json). Source-only, no deployed-runtime claim. |
| Existing planning activity regression |3 tests pass | Status consistency only. |

Private empty-form screenshots from the final pass remain in `.scratch/shb-browser-resume-pPw1Po02`. The earlier controlled failure diagnostic is `.scratch/shb-browser-resume-yrKlSctK/browser-failure.json`. No raw invitation/capture or scratch evidence is staged. All owned browser/demo/test contexts exited; no service remains running.

## Reproducible commands

No .env or real credentials are needed. Existing task-owned scratch/cache paths are used; browser TMPDIR is now independently short and private.

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb.py --shared
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#browser --command python3 scripts/demo_shb.py --check --browser --release .scratch/shb-private-resume-t2p3r5cc/release
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos#backend --command python3 scripts/check_shb_source.py
python3 -m unittest discover -s tests -p 'test_planning_activity.py'
```

For fresh private static output, run the existing helper in the pinned frontend shell with a new empty destination under an owned `.scratch` parent, then compile its manifest:

```sh
env TMPDIR="$PWD/.scratch/auth-unicode-tmp" XDG_CACHE_HOME="$PWD/.scratch/phase2-repro-nix-cache" nix develop --offline ./ops/nixos --command python3 - <<'BUILD'
from pathlib import Path
import sys,tempfile,subprocess
sys.path.insert(0,'scripts')
from check_browser_public import build_public
parent=Path(tempfile.mkdtemp(prefix='shb-private-resume-',dir=Path('.scratch').resolve()))
release=parent/'release';release.mkdir(mode=0o700)
build_public(release)
subprocess.run([sys.executable,'scripts/compile_shb_release.py','--dist',str(release)],check=True)
print(release)
BUILD
```

Pass the printed release path to `demo_shb.py --check --browser --release` or the usable `--serve --release` mode in place of `--check --browser`. Open the invitation from the private file named by `--serve`, use Synthetic Company Limited and a synthetic.invalid contact, and stop with Ctrl-C. Never publicly serve the release directory.

FPGA Checkout remains disabled; coupons, ASIC assigned reviewed offers, paid-order finalization, staff order view and ordinary transaction/request notification integration remain unfinished. Continue the existing07-02 slice. The support team tracks usage and sends task emails manually. Approved commercial/provider values, independent runtime/recovery and all actual host/ingress/release qualifications remain pending in the one register `docs/decisions.md`; these local proofs neither satisfy nor authorize them. No actual bank/mail/DNS/TLS/storage/host action or paid provision occurred.
