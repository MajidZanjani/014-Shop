---
status: complete
---
# Stable control-record descriptor reads

Code5330962 adds before/after metadata equality and exact nonempty read-length enforcement before parsing root-owned control files. Tests cover changed device/inode/UID/GID/mode/size/mtime/ctime, truncated and empty reads, exact32768-byte input and existing positive/denial cases.

Local checks passed: process18 tests; deployment-eval15/29; database-tools6/5; operator-runtime4/10. No failure; ignored Nix concurrent eval-cache busy warning. git diff --check passed. Exact package bytes rebuilt by packaged lanes. No actual host connection, record publication, service/resource change or credentials needed.

This bounded fix is complete; plan14 and Phase02 are not. Metadata checks do not establish atomic generation publication or protection against a privileged writer. Remaining implementation and off-host qualification persist in STATE and phase PARTIAL records. One-shot pause files consumed on successful resume; original checkpoint remains in Git. Dependency approval audit reconciled against actual JSON and explicitly historical summary section.
