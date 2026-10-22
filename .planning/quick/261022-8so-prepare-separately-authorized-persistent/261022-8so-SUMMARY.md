---
status: complete
---
# Library-only persistent admission block

Prepared an exact-authority root-only blocking precursor. It locks the existing permanent admission inode exclusively, binds the original admitted raw hash, writes blocked bytes only, fsyncs/reads back and rechecks authority. It creates/provisions/publishes/reopens nothing and never repairs or retries uncertain state. Flags retain false durability qualification and publication/retry/reopening authority.

Actual owned-scratch SQL/barrier suite3 checks/128 tests10.148s; source7/5 in4.747s; operator7/17 in6.720s; native54/9 write1.307s pass. Five added tests cover closed/expired/exact authority, root denial, reader exclusion, unchanged inode/persistent block, revocation, short/zero writes/sync failures and repeat denial. No failing run. Root authority mocked, fixed path adapted; no actual host/custody/storage durability claim.

Full publisher/generation/custody/reopening, app coverage, roles/runtime and independent qualification remain pending.14/16/17/full phase incomplete. No real credential/host/provider/service/resource action. Historical immutable reports retained. Commit/push within the existing scoped origin/main authorization.
