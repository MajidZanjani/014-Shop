# Shop-only user generator discovery candidate

The disabled shop module emits no discovery drop-in. When explicitly enabled
with the existing reviewed-inventory/activation and unused-identity assertions,
the candidate declares exactly one root-owned instance drop-in:
`/etc/systemd/system/user@UID.service.d/50-shop-generators.conf`.
It sets `SYSTEMD_GENERATOR_PATH` to a single immutable Nix-store link farm
containing `podman-user-generator`, pointing to the existing pinned wrapper.
The same bundle is exposed through `/etc/xspi-shop/runtime/user-generators`.

This replaces the generator search list for only the new shop user manager.
There is no trailing colon/default search append, shared user@.service template
change, global user generator installation or mutable home-directory installer.
Other default unit generators for that new account are deliberately excluded;
environment generators and ordinary unit search paths are not changed. The
shop generator invokes the existing cleared-environment Quadlet wrapper with
its exact account unit directory. The wrapper still enforces account/runtime
preflight and guarded Podman calls; this change does not bypass those checks.

The upstream [systemd environment interface](https://www.freedesktop.org/software/systemd/man/latest/systemd.html#Environment)
documents generator search replacement and the distinct trailing-colon append
behavior. Documentation describes the interface; actual compatibility with the
pinned systemd260.5/Podman candidate and existing host lifecycle is still pending.
No manager was started/reloaded and no generator, Podman container or NixOS
activation was run. No host filesystem configuration was installed.

Pure Nix evaluation verifies that disabled configuration emits no shop discovery
artifact, enabled configuration has only the exact new UID instance drop-in,
the drop-in points at its own actual bundle and global generators are unchanged.
A synthetic existing9908 account/manager sentinel remains unchanged while the
new9909 fixture is admitted. Negative controls deny root/other/template instance
paths, mutable/multi-directory/default-appended searches, extra Environment or
ExecStart settings, other sections and inherited DEFAULT fields. Existing
shell/TOML/storage/probe/deployment controls remain required.

Before installation: actual protected-host inventory, unused account/range and
path ownership, exact resource allowlist, NixOS activation-impact review and
scoped host action authority are still required. Starting a new manager or
applying this instance environment is an explicit reviewed shop lifecycle step;
this source declaration supplies no reload/restart permission. Shop-only rollback
must preserve committed records and pre-existing resources. Off-host actual
manager discovery, Quadlet generation, resource containment and lifecycle tests
remain pending. This is preparation, not runtime qualification or phase acceptance.
