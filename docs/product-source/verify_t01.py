#!/usr/bin/env python3
"""Read-only T01 documentation contracts; Python standard library only."""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = "SLL-xSPI-MC-Shop-Proposal-2026-10-20.md"
HANDOFF = "SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-20.md"
PRODUCT = "docs/product-source/SLL_xSPI_MC_Product_Page.md"
MATRIX = ".planning/SOURCE-MATRIX.md"
REQS = ".planning/REQUIREMENTS.md"
LEDGER = ".planning/SOURCES.md"
IDENTITIES = {
    PROPOSAL: (201117, "d8db6b54e3e887ca940f0faff0949ca1a1fa2ce24c26075aabd78925f0f60356"),
    HANDOFF: (42140, "60e6af0fce6db7412408e04eceb0283881585a295f45cbba0607c4bde9f4227e"),
    PRODUCT: (23969, "562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263"),
}
TRACE = "| family-1-1 | Altera / Intel FPGA → Cyclone 10 LP (C10LP) | product §1 / Altera, lines 17–29; proposal FPGA vendors and families, line 105 | Altera / Intel FPGA; family order 1; altera-cyclone-10-lp-c10lp | SRC-02 Phase 1; CAT-02 Phase 3 | Specified draft; coverage relationship unresolved; implementation pending |"

class ContractError(ValueError):
    pass

def require(ok, name):
    if not ok:
        raise ContractError(name)
    return 1

def text(data, name):
    require(data is not None and len(data) > 0, name + ": missing/empty")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise ContractError(name + ": invalid UTF-8") from None

def appendix(data):
    value = text(data, "proposal appendix")
    marker = "## Product source snapshot\n"
    require(value.count(marker) == 1, "appendix heading uniqueness")
    tail = value.split(marker, 1)[1]
    blocks = re.findall(r"^\x60{4}markdown\n(.*?)^\x60{4}\s*$", tail, re.M | re.S)
    require(len(blocks) == 1, "bounded appendix uniqueness")
    return blocks[0].encode("utf-8")

def source(inputs):
    count = 0
    for name, (size, digest) in IDENTITIES.items():
        data = inputs.get(name)
        text(data, name)
        count += require(len(data) == size, name + ": byte length")
        count += require(hashlib.sha256(data).hexdigest() == digest, name + ": SHA-256")
        count += require(data.endswith(b"\n"), name + ": final newline")
        count += require(digest in text(inputs.get(LEDGER), LEDGER), "ledger identity")
    count += require(appendix(inputs[PROPOSAL]) == inputs[PRODUCT], "appendix equality")
    matrix = text(inputs.get(MATRIX), MATRIX)
    count += require(matrix.splitlines().count(TRACE) == 1, "family tracer complete path")
    product = inputs[PRODUCT].decode().splitlines()
    proposal = inputs[PROPOSAL].decode().splitlines()
    count += require("Altera / Intel FPGA" in product[16] and product[24] == "### Altera / Intel FPGA"
                     and product[28] == "- [ ] Cyclone 10 LP (C10LP)", "product locator 17–29")
    row = "| Altera / Intel FPGA | 1 | Cyclone 10 LP (C10LP) | " + chr(96) + "altera-cyclone-10-lp-c10lp" + chr(96) + " |"
    count += require(proposal[104] == row and row in matrix.splitlines(), "proposal/matrix family row")
    reqs = text(inputs.get(REQS), REQS)
    for identity, phase in (("SRC-02", 1), ("CAT-02", 3)):
        count += require(f"**{identity}**:" in reqs and f"| {identity} | Phase {phase} | Pending |" in reqs,
                         identity + ": requirement/owning phase")
    return count

def load_source():
    return {name: (ROOT / name).read_bytes() if (ROOT / name).is_file() else None
            for name in (*IDENTITIES, MATRIX, REQS, LEDGER, ".planning/ROADMAP.md")}


SCOPE = "docs/product-source/t01-scope.md"
IDS = ("sll-xspi-mc", "sll-xspi-mc-support-10h", "sll-xspi-mc-v1",
       "https://shop.xspi.pro", "https://shop-admin.xspi.pro")
SCOPE_FACTS = (
    "Old task numbers provide no new completion credit.",
    "Recoverable Git history is retained.",
    "Unrelated work is preserved.",
    "External state is uninspected.",
    "No application/data migration identified within the inspected checkout.",
    "FLAGGED SRC-04/unclassified remains for end-of-phase human review.",
)

def scope(data):
    import json
    value = text(data, "scope")
    count = 0
    for item in (*IDS, *SCOPE_FACTS):
        count += require(item in value, "scope identity/reset boundary: " + item)
    match = re.findall(r"\x60{3}json\n(.*?)\n\x60{3}", value, re.S)
    require(len(match) == 1, "scope metadata block")
    try:
        meta = json.loads(match[0])
    except ValueError:
        raise ContractError("scope metadata JSON") from None
    for field in ("observed_utc", "head", "branch", "root", "worktrees", "status", "ignore", "inventory", "isolation"):
        count += require(field in meta, "scope metadata: " + field)
    count += require(bool(re.fullmatch(r"[0-9a-f]{40}", meta["head"])), "scope revision")
    count += require(bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", meta["observed_utc"])), "scope timestamp")
    count += require(meta["ignore"] == ".env" and bool(meta["inventory"]), "scope path inventory/ignore")
    if meta["isolation"] == "fulfilled":
        branch = meta["branch"]
        count += require(bool(re.fullmatch(r"((worktree-)?agent-|worktree-wf_)[A-Za-z0-9._/-]+", branch)), "scope isolated branch")
        blocks = meta["worktrees"].strip().split("\n\n")
        count += require(any(f"worktree {meta['root']}\nHEAD {meta['head']}\nbranch refs/heads/{branch}" in block
                             for block in blocks), "scope matching worktree/revision/branch")
    else:
        count += require(meta["isolation"] == "pending" and bool(meta.get("isolation_gate")), "scope pending isolation gate")
        print("GATE: isolation pending; full T01 acceptance withheld")
    return count


# Bounded tables from the immutable proposal, before its embedded appendix.
# Complete row comparison preserves requiredness/defaults as well as labels.
GROUPS = (
    ("vendor", 98, 102, 3, 1, "CAT-02", 3),
    ("family", 104, 118, 13, 2, "CAT-02", 3),
    ("term", 124, 128, 3, 1, "CAT-02", 3),
    ("band", 137, 140, 4, 1, "CAT-02", 3),
    ("access", 150, 151, 2, 1, "AUTH-04", 6),
    ("control", 167, 179, 13, 1, "SHOP-02", 4),
    ("business", 189, 207, 19, 1, "COM-04", 7),
    ("declaration", 219, 222, 4, 1, "COM-05", 7),
    ("marketing", 223, 223, 1, 1, "AUTH-06", 6),
    ("reset", 249, 264, 14, 0, "SHOP-02", 4),
)
TRACE_HEADING = "## Complete bounded record traceability"

def cells(line):
    return [part.strip() for part in line.strip().strip("|").split("|")]

def proposal_records(inputs):
    lines = text(inputs.get(PROPOSAL), PROPOSAL).splitlines()
    records = []
    for group, start, end, expected, label_at, req, phase in GROUPS:
        rows = [(n, line) for n, line in enumerate(lines, 1)
                if start <= n <= end and line.startswith("| ")
                and not line.startswith("|---") and not line.startswith("| ---")]
        # Header rows are excluded by numeric first cell, except the reset table.
        rows = [(n, line) for n, line in rows
                if (cells(line)[0].isdigit() or group == "family"
                    or (group == "reset" and cells(line)[0] != "Customer change"))]
        require(len(rows) == expected, group + ": bounded source count")
        heading = next(line.lstrip("# ") for line in reversed(lines[:start])
                       if line.startswith("#"))
        for ordinal, (n, line) in enumerate(rows, 1):
            row = cells(line)
            label = row[label_at]
            if group == "family":
                label = row[0] + " → " + label
            contract = " / ".join(row)
            records.append((group + "-" + str(ordinal), label,
                            f"{PROPOSAL} §{heading}, lines {n}–{n}", contract,
                            f"SRC-02 Phase 1; {req} Phase {phase}", line))
    helper_line = next(n for n, line in enumerate(lines[:230], 1)
                       if line.startswith("Two additional convenience controls"))
    for i, label in enumerate(("Same as registered address", "Same as purchasing contact"), 1):
        records.append((f"helper-{i}", label,
                        f"{PROPOSAL} §Business checkout, lines {helper_line}–{helper_line}",
                        "Independent convenience helper; proposed linked-state enforcement",
                        "SRC-02 Phase 1; COM-04 Phase 7", None))
    return records

def trace_lines(inputs):
    return ["| " + " | ".join((*record[:5],
             "Written draft; proposed enforcement only; unresolved approvals remain pending")) + " |"
            for record in proposal_records(inputs)]

def inventory(inputs):
    matrix = text(inputs.get(MATRIX), MATRIX)
    count = 0
    require(matrix.count(TRACE_HEADING) == 1, "complete inventory section")
    section = matrix.split(TRACE_HEADING, 1)[1]
    actual = [line for line in section.splitlines()
              if re.match(r"\| (vendor|family|term|band|access|control|business|declaration|marketing|reset|helper)-", line)]
    expected = trace_lines(inputs)
    count += require(actual == expected and len(actual) == 78, "exact complete ordered trace records")
    original = matrix.split(TRACE_HEADING)[0].splitlines()
    product = text(inputs.get(PRODUCT), PRODUCT)
    reqs = text(inputs.get(REQS), REQS)
    roadmap = text(inputs.get(".planning/ROADMAP.md"), "roadmap")
    for identity, label, locator, contract, links, row in proposal_records(inputs):
        if row:
            count += require(original.count(row) == 1, identity + ": original matrix row")
        # Exact source wording is retained; configuration purpose labels and resets
        # originate in the proposal, not literal product input labels.
        if identity.split("-")[0] in ("family", "vendor", "term", "access", "business", "declaration", "marketing"):
            raw_label = label.split(" → ")[-1]
            count += require(raw_label in product, identity + ": embedded product label")
        for req, phase in re.findall(r"([A-Z]+-\d+) Phase (\d+)", links):
            count += require(f"**{req}**:" in reqs and f"| {req} | Phase {phase} |" in reqs
                             and f"### Phase {phase}:" in roadmap, identity + ": requirement ownership")
    return count


def self_check():
    import contextlib
    import io
    import json
    inputs = load_source()
    scope_bytes = (ROOT / SCOPE).read_bytes()
    require(source(inputs) > 0 and scope(scope_bytes) > 0, "valid controls")
    rejected = 0

    def reject(name, callback):
        nonlocal rejected
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                callback()
        except ContractError:
            rejected += 1
            print("PASS rejection: " + name)
        else:
            raise ContractError("unexpected accepted mutation: " + name)

    for name, bad in (("missing", None), ("empty", b""), ("encoding", b"\xff"),
                      ("altered byte", b"X" + inputs[PRODUCT][1:]),
                      ("final newline", inputs[PRODUCT][:-1])):
        candidate = dict(inputs)
        candidate[PRODUCT] = bad
        reject(name, lambda candidate=candidate: source(candidate))
    proposal = inputs[PROPOSAL]
    marker = b"\x60\x60\x60\x60markdown\n"
    at = proposal.index(marker, proposal.index(b"## Product source snapshot\n")) + len(marker)
    changed = proposal[:at] + b"X" + proposal[at+1:]
    reject("appendix equality independent of package hash",
           lambda: require(appendix(changed) == inputs[PRODUCT], "appendix equality"))
    for name, old, new in (
        ("missing tracer", TRACE, ""),
        ("wrong family locator", "lines 17–29", "lines 18–30"),
        ("wrong requirement phase", "SRC-02 Phase 1", "SRC-02 Phase 3"),
    ):
        candidate = dict(inputs)
        candidate[MATRIX] = inputs[MATRIX].decode().replace(old, new).encode()
        reject(name, lambda candidate=candidate: source(candidate))
    for name, old in (("wrong product", "sll-xspi-mc"), ("wrong origin", "https://shop.xspi.pro"),
                      ("missing reset", SCOPE_FACTS[0])):
        reject(name, lambda old=old: scope(scope_bytes.decode().replace(old, "WRONG").encode()))
    meta_match = re.search(r"\x60{3}json\n(.*?)\n\x60{3}", scope_bytes.decode(), re.S)
    meta = json.loads(meta_match[1])

    def scope_candidate(candidate):
        return (scope_bytes.decode()[:meta_match.start(1)] + json.dumps(candidate) +
                scope_bytes.decode()[meta_match.end(1):]).encode()

    for field in ("head", "branch", "worktrees", "observed_utc", "status"):
        candidate = dict(meta)
        del candidate[field]
        reject("missing metadata " + field, lambda candidate=candidate: scope(scope_candidate(candidate)))
    for field, value in (("branch", "main"), ("worktrees", "worktree /wrong\nHEAD " + meta["head"]),
                         ("head", "0" * 40)):
        candidate = dict(meta, isolation="fulfilled")
        candidate[field] = value
        reject("unsupported isolation " + field, lambda candidate=candidate: scope(scope_candidate(candidate)))
    candidate = dict(meta, isolation="pending", isolation_gate="Separate branch not established")
    with contextlib.redirect_stdout(io.StringIO()):
        require(scope(scope_candidate(candidate)) > 0, "honest pending control")
    require(inventory(inputs) > 0, "valid inventory control")
    trace = trace_lines(inputs)
    for name, old, new in (
        ("omitted group", "\n".join(trace[38:57]), ""),
        ("empty inventory", TRACE_HEADING, ""),
        ("label substitution", trace[4], trace[4].replace("MAX 10", "MAX 99")),
        ("family order", "\n".join(trace[4:6]), "\n".join(reversed(trace[4:6]))),
        ("merged Cyclone", trace[5], ""),
        ("merged repeated host control", trace[32], ""),
        ("requiredness changed", trace[55], trace[55].replace("Short description", "Required")),
        ("marketing mandatory declaration", "| marketing-1 |", "| declaration-5 |"),
        ("extra record", trace[-1], trace[-1] + "\n" + trace[-1]),
        ("locator changed", trace[0], trace[0].replace("99–99", "98–98")),
        ("requirement changed", trace[0], trace[0].replace("CAT-02 Phase 3", "CAT-02 Phase 7")),
    ):
        candidate = dict(inputs)
        require(old in inputs[MATRIX].decode(), "mutation exercised: " + name)
        candidate[MATRIX] = inputs[MATRIX].decode().replace(old, new).encode()
        reject(name, lambda candidate=candidate: inventory(candidate))
    for mode in ("decisions", "all"):
        reject("unimplemented " + mode, lambda mode=mode: dispatch(mode))
    require(rejected > 0, "positive rejection count")
    print(f"PASS self-check: {rejected} asserted rejections; valid source/scope and pending controls passed")

def dispatch(mode):
    if mode == "source":
        print(f"PASS source: {source(load_source())} executed checks (local documentation only)")
    elif mode == "scope":
        print(f"PASS scope: {scope((ROOT / SCOPE).read_bytes())} executed checks (local documentation only)")
    elif mode == "inventory":
        print(f"PASS inventory: {inventory(load_source())} executed checks; 78 trace records")
    elif mode == "self-check":
        self_check()
    else:
        raise ContractError("unimplemented mode: " + mode)

def main():
    dispatch(sys.argv[1] if len(sys.argv) == 2 else "")

if __name__ == "__main__":
    try:
        main()
    except (ContractError, OSError) as exc:
        print(f"FAIL T01: {exc}", file=sys.stderr)
        sys.exit(1)
