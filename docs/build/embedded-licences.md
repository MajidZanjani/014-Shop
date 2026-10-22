# Embedded Python licence evidence

The exact wheels for pip-requirements-parser32.0.1 and packageurl-python0.17.6
include MIT grant, condition and disclaimer text in leading source comments.
The named-file audit correctly found no standalone LICENSE/NOTICE files; it did
not inspect these embedded headers. Preserve that historical report and the
original licences.json/SBOM bytes unchanged.

`scripts/retain_embedded_licences.py` verifies each retained wheel digest before
shared bounded archive validation and reads only two explicitly selected paths:
`pip_requirements_parser.py` and `packageurl/__init__.py`. It retains the exact
leading blank/comment bytes, including copyright holder lines, without stripping
comment markers or normalizing line endings. `embedded-licences.json` records
source inventory SHA256, distribution identity/digest, archive SHA256, complete
source member SHA256, start/end byte offsets and retained text hash/path.
The content-addressed text files are supplementary evidence, not replacement
licence files represented as having existed in the wheel.

Actual October22 collection and independent recheck observed both headers.
These observations address evidence discovery for two Python-tool findings.
They do not complete review of every incorporated component or source notice,
author references, package-wide redistribution obligations or legal acceptance.
Ten npm text findings, native/Nix/OCI coverage and full inventory remain pending.
The original twelve named-file findings remain historical evidence; current
assessment includes this supplemental report. No INVENTORY_PASS is claimed.

Run `python3 -B scripts/retain_embedded_licences.py` to download, verify and compare
retained evidence. `--write` is exclusive creation only; existing/partial outputs
are retained for review, never repaired or overwritten automatically. This is
not crash-durable publication. Leading comments are bounded to16KiB and selected
source members to1MiB; shared archive limits/path/link/duplicate checks apply.
The fixed identity/path policy deliberately fails if retained Python gap targets
change; a future scope change requires explicit code/evidence review.

Tests cover exact bytes including CRLF, missing clauses/copyright holder,
nonleading text, bounds, wheel integrity, missing/invented identities or source
members and the unresolved approval/completeness flags. Marker checks establish
observed candidate text for review, not automated legal classification.
