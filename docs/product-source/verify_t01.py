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
            for name in (*IDENTITIES, MATRIX, REQS, LEDGER)}


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
    for mode in ("inventory", "decisions", "all"):
        reject("unimplemented " + mode, lambda mode=mode: dispatch(mode))
    require(rejected > 0, "positive rejection count")
    print(f"PASS self-check: {rejected} asserted rejections; valid source/scope and pending controls passed")

def dispatch(mode):
    if mode == "source":
        print(f"PASS source: {source(load_source())} executed checks (local documentation only)")
    elif mode == "scope":
        print(f"PASS scope: {scope((ROOT / SCOPE).read_bytes())} executed checks (local documentation only)")
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
