# Exact-distribution licence gap audit

`scripts/audit_licence_gaps.py` examines the distributions for every empty
`licence_texts` record in the retained `docs/evidence/t02/licences.json`.
It leaves that file and all raw/derived SBOMs unchanged.

The October 22 audit downloaded all twelve artifacts from their exact official
npm/Python distribution URLs and verified each retained SRI/SHA256 digest before
archive inspection. Ten npm tarballs and two Python-tool wheels contained no
separately named licence/notice candidate under the documented filename rules.
This supports the existing missing-file findings; it does not establish absence
of legal text inside README, metadata, source headers or binary payloads.

`docs/evidence/t02/licence-gap-audit.json` binds the source inventory hash, exact
artifact identity/digest, observed archive SHA256 and complete member names,
sizes and types. It records zero named candidates and keeps inventory_complete
and legal_approval false. No package installation or execution occurred. No
source notice, licence substitute, upstream compatibility or legal approval is
inferred. Original twelve findings remain unresolved. Native/Nix/OCI closure,
redistribution requirements, image layers and runtime review remain pending.

Run `python3 -B scripts/audit_licence_gaps.py` to fetch, verify and compare the
retained report again. `--write` exclusively creates new evidence and refuses
existing output; it does not overwrite/repair partial evidence. Report creation
is not a crash-durable publication protocol. Candidate text files, if any, use
content hashes beneath `licence-gap-texts/`; none was produced in this audit.

The scanner uses HTTPS requests restricted to exact registry origins, no proxies
or redirects, a 30-second request timeout and a 64 MiB compressed-byte limit.
It never extracts archives. It rejects duplicate/unsafe member names, links and
special members, more than 20,000 members, declared expanded totals over 256 MiB
and candidate files over 10 MiB. Named candidates match LICENSE/LICENCE,
LICENSES/LICENCES, COPYING, COPYRIGHT or NOTICE, optionally followed by a dot,
underscore or hyphen suffix. This is a named-file audit, not an exhaustive legal
text classifier or recursive native dependency scan.

Next work: inspect attributable embedded/source notice evidence for each exact
version, preserve the distinction between distribution-incorporated and external
source notices, and prepare outstanding native/OCI provenance. Do not copy a
generic MIT/ISC text into the inventory as if it was incorporated in a package.
