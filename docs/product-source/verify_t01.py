#!/usr/bin/env python3
"""Read-only T01 documentation contracts; Python standard library only."""
import hashlib
import re
import sys
import subprocess
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
        count += require(f"**{identity}**:" in reqs and bool(re.search(rf"^\| {re.escape(identity)} \| Phase {phase} \| (?:Pending|In Progress|Complete|Blocked) \|$", reqs, re.M)),
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
    actual = [line for line in section.splitlines() if line.startswith("|")][2:]
    expected = trace_lines(inputs)
    count += require(actual == expected and len(actual) == 78, "exact complete ordered trace records")
    original = matrix.split("## Row-level source traceability")[0].splitlines()
    original_tables = [line for line in "\n".join(original).split("## Exact option inventory", 1)[1].splitlines() if line.startswith("|")]
    source_tables = [line for line in text(inputs.get(PROPOSAL), PROPOSAL).splitlines()[92:264] if line.startswith("|")]
    count += require(original_tables == source_tables, "original exact ordered inventory tables")
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


DECISIONS = "docs/decisions.md"
PHASES = ("T03/T07/T10/T14", "T03/T07/T14", "T03/T07/T10/T14",
          "T03/T06/T07/T10/T14", "T03/T07/T10/T14", "T10/T14", "T09/T14",
          "T03/T07/T08/T10/T14", "T11/T12/T14", "T11/T14", "T11/T14", "T06/T10/T12/T14")
ROLES = ("SLL engineering/product", "SLL commercial/finance",
         "SLL commercial/legal + engineering", "SLL licensing/engineering",
         "SLL support/commercial/finance", "SLL engineering/licensing",
         "SLL finance + selected acquirer", "SLL commercial/legal + tax adviser",
         "SLL privacy/operations + recovery custodian", "SLL infrastructure/billing owner",
         "SLL DNS/infrastructure owner", "SLL email/operations + business owners")
DECISION_HEADER = ["ID", "Decision or supplied fact", "Recommended handling", "Affected phase(s)",
                   "Operation actually blocked", "Proposed owner", "Status", "Approval evidence"]

def decisions(data, inputs):
    value = text(data, "decisions")
    lines = [line for line in value.splitlines() if line.startswith("|")]
    count = require(len(lines) == 14, "one complete decision table")
    count += require(cells(lines[0]) == DECISION_HEADER, "decision header")
    count += require(len(cells(lines[1])) == 8 and all(re.fullmatch(r"-+", c) for c in cells(lines[1])),
                     "decision delimiter width")
    source_rows = [cells(line) for line in text(inputs.get(HANDOFF), HANDOFF).splitlines()
                   if re.match(r"\| P-\d\d \|", line)]
    require(len(source_rows) == 12, "bounded authoritative P register")
    rows = [cells(line) for line in lines[2:]]
    count += require([row[0] for row in rows] == [f"P-{i:02}" for i in range(1, 13)],
                     "ordered unique complete decisions")
    for i, row in enumerate(rows):
        count += require(len(row) == 8 and all(row), "decision width/nonempty fields")
        count += require(row[:3] == source_rows[i][:3], "decision source meaning")
        count += require(row[3] == PHASES[i], "decision affected phases")
        count += require(row[4].startswith(source_rows[i][3]) and "Preparation continues:" in row[4],
                         "decision operation and unaffected preparation")
        count += require(row[5] == ROLES[i], "responsible role only")
        count += require(row[6] in ("Pending", "Approved"), "decision status")
        if row[6] == "Pending":
            count += require(row[7] == "None supplied", "pending evidence")
        else:
            # This validates evidence structure, never the authority of an approval.
            count += require(all(re.search(key + r":\s*[^;]+", row[7])
                                 for key in ("Approver", "Date", "Scope", "Revision", "Evidence"))
                             and bool(re.search(r"Date: \d{4}-\d\d-\d\d", row[7])),
                             "dated scoped attributable approval required")
    return count


EVIDENCE = "docs/implementation-evidence.md"
CHECKER = "docs/product-source/verify_t01.py"
ARTIFACTS = (CHECKER, MATRIX, DECISIONS, SCOPE, LEDGER)
GATES = ("FLAGGED SRC-04/unclassified", "source intent", "approval scope", "execution isolation",
         "source preservation prohibition", "pending decisions prohibition", "T02–T14 remain unexecuted")

def evidence_record(data):
    """Bound the dated T01 record within the shared evidence document."""
    value = text(data, "implementation evidence")
    headings = list(re.finditer(r"^#{1,2} T(\d{2})\b[^\n]*$", value, re.M))
    own = [heading for heading in headings if heading[1] == "01"]
    require(len(own) == 1, "one bounded T01 record")
    start = own[0].start()
    end = next((heading.start() for heading in headings if heading.start() > start), len(value))
    return value[start:end], start, end


def historical_artifacts(revision):
    """Read only the five allowlisted artifacts from an attributable Git commit."""
    require(isinstance(revision, str) and bool(re.fullmatch(r"[0-9a-f]{40}", revision)),
            "historical artifact commit identity")
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", revision, "HEAD"],
                              cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    require(ancestor.returncode == 0, "historical artifact commit reachable")
    result = {}
    for name in ARTIFACTS:
        saved = subprocess.run(["git", "show", f"{revision}:{name}"], cwd=ROOT,
                               capture_output=True, timeout=5)
        require(saved.returncode == 0, "historical artifact available: " + name)
        result[name] = saved.stdout
    return result


def evidence(data, inputs):
    import json
    value = evidence_record(data)[0]
    blocks = re.findall(r"\x60{3}json\n(.*?)\n\x60{3}", value, re.S)
    require(len(blocks) == 1, "one evidence metadata block")
    try:
        meta = json.loads(blocks[0])
    except ValueError:
        raise ContractError("evidence JSON") from None
    count = 0
    for field in ("observed_utc", "head", "branch", "root", "status", "environment",
                  "tasks", "commands", "artifacts", "artifact_revision", "isolation", "acceptance"):
        count += require(field in meta and meta[field] is not None, "evidence field: " + field)
    count += require(bool(re.fullmatch(r"[0-9a-f]{40}", meta["head"])), "evidence head")
    count += require(bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", meta["observed_utc"])), "evidence timestamp")
    count += require(bool(re.fullmatch(r"((worktree-)?agent-|worktree-wf_)[A-Za-z0-9._/-]+", meta["branch"]))
                     and isinstance(meta["root"], str) and Path(meta["root"]).is_absolute()
                     and Path(meta["root"]).name == meta["branch"].removeprefix("worktree-"),
                     "evidence historical worktree identity")
    count += require(meta["acceptance"] == "conditional manual review"
                     and meta["isolation"] == "separate worktree observed; manual judgment pending",
                     "conditional acceptance/isolation")
    count += require(list(meta["tasks"]) == [f"01-{p:02}-{t:02}" for p in (1, 2) for t in (1, 2, 3)]
                     and all(meta["tasks"].values()), "six task statuses")
    recorded = historical_artifacts(meta["artifact_revision"])
    for name in ARTIFACTS:
        count += require(meta["artifacts"].get(name) == hashlib.sha256(recorded[name]).hexdigest(),
                         "evidence artifact revision: " + name)
    for mode in ("source", "scope", "inventory", "decisions"):
        observation = meta["commands"].get(mode, {})
        count += require(observation.get("exit") == 0 and observation.get("checks", 0) > 0
                         and observation.get("command") == f"python3 {CHECKER} {mode}",
                         "observed positive command: " + mode)
    for name in (MATRIX, DECISIONS, SCOPE, CHECKER, LEDGER):
        count += require(name in value, "evidence artifact link: " + name)
    for gate in GATES:
        count += require(gate in value, "remaining gate: " + gate)
    count += require(EVIDENCE in text(inputs.get(LEDGER), LEDGER), "source ledger evidence link")
    return count

def all_contracts(inputs):
    results = {"source": source(inputs), "scope": scope(inputs.get(SCOPE)),
               "inventory": inventory(inputs), "decisions": decisions(inputs.get(DECISIONS), inputs),
               "evidence": evidence(inputs.get(EVIDENCE), inputs)}
    require(all(count > 0 for count in results.values()), "nonempty required modes")
    return results

def load_all():
    inputs = load_source()
    for name in (SCOPE, DECISIONS, EVIDENCE, CHECKER):
        inputs[name] = (ROOT / name).read_bytes() if (ROOT / name).is_file() else None
    return inputs


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
        register = (ROOT / DECISIONS).read_bytes()
    require(decisions(register, inputs) > 0, "valid pending register control")
    require(decisions(register, inputs) > 0 and (ROOT / DECISIONS).read_bytes() == register,
            "repeated read-only decisions")
    rows = [line for line in register.decode().splitlines() if line.startswith("| P-")]
    for name, old, new in (
        ("malformed six-cell baseline", rows[0], rows[0].replace(" | " + PHASES[0], "").replace(" | " + ROLES[0], "  " + ROLES[0])),
        ("duplicate decision", rows[1], rows[0]),
        ("omitted decision", rows[1], ""),
        ("missing role", " | " + ROLES[0] + " |", " |  |"),
        ("missing phase scope", " | " + PHASES[0] + " |", " |  |"),
        ("missing operation", rows[0], " | ".join(rows[0].split(" | ")[:5] + [""] + rows[0].split(" | ")[6:])),
        ("shifted status", "| Pending | None supplied |", "| None supplied | Pending |"),
        ("unsupported approval", "| Pending | None supplied |", "| Approved | None supplied |"),
    ):
        require(old in register.decode(), "decision mutation exercised: " + name)
        reject(name, lambda old=old, new=new: decisions(register.decode().replace(old, new).encode(), inputs))
    complete = load_all()
    require(all_contracts(complete)["evidence"] > 0, "valid all/evidence controls")
    for path in (PROPOSAL, PRODUCT, MATRIX, DECISIONS, SCOPE, EVIDENCE):
        candidate = dict(complete)
        candidate[path] = None
        reject("all missing " + path, lambda candidate=candidate: all_contracts(candidate))
    ev = complete[EVIDENCE]
    _, begin, end = evidence_record(ev)
    match = re.compile(r"\x60{3}json\n(.*?)\n\x60{3}", re.S).search(ev.decode(), begin, end)
    metadata = json.loads(match[1])
    future_ledger = dict(complete)
    future_ledger[LEDGER] += b"\nT02 evidence link added after T01 execution.\n"
    require(all_contracts(future_ledger)["evidence"] > 0, "shared ledger advances without rewriting T01")
    future_record = dict(complete)
    future_record[EVIDENCE] += b'\n## T02 local documentation evidence\n\n```json\n{"phase": "02"}\n```\n'
    require(all_contracts(future_record)["evidence"] > 0, "later phase JSON stays outside T01 metadata")
    duplicate = ev + b'\n```json\n{}\n```\n'
    reject("duplicate T01 metadata", lambda: evidence(duplicate, complete))
    unknown_revision = dict(metadata, artifact_revision="0" * 40)
    unknown_bytes = (ev.decode()[:match.start(1)] + json.dumps(unknown_revision) + ev.decode()[match.end(1):]).encode()
    reject("unavailable historical artifact revision", lambda: evidence(unknown_bytes, complete))
    future_decisions = dict(complete)
    future_decisions[DECISIONS] = register.decode().replace("| Pending | None supplied |", "| Approved | Approver: fixture; Date: 2026-10-20; Scope: fixture only; Revision: synthetic; Evidence: in-memory control |", 1).encode()
    require(all_contracts(future_decisions)["evidence"] > 0, "valid later register revision preserves T01 snapshot")
    # Evidence describes its original execution, even after merge/relocation.
    relocated = dict(metadata, root="/tmp/retained-t01/" + metadata["branch"].removeprefix("worktree-"))
    candidate_bytes = (ev.decode()[:match.start(1)] + json.dumps(relocated) + ev.decode()[match.end(1):]).encode()
    require(evidence(candidate_bytes, complete) > 0, "historical evidence survives checkout relocation")
    for label, changes in (("relative recorded root", {"root": "relative"}),
                           ("root/branch mismatch", {"root": "/tmp/unrelated-checkout"}),
                           ("non-isolated recorded branch", {"branch": "main"})):
        candidate = dict(metadata, **changes)
        bad = (ev.decode()[:match.start(1)] + json.dumps(candidate) + ev.decode()[match.end(1):]).encode()
        reject(label, lambda bad=bad: evidence(bad, complete))
    for status in ("In Progress", "Complete", "Blocked"):
        candidate = dict(inputs)
        candidate[REQS] = inputs[REQS].decode().replace("| Phase 1 | Pending |", f"| Phase 1 | {status} |").encode()
        require(source(candidate) > 0, "requirement lifecycle status preserves provenance")
    for field in ("head", "tasks", "artifacts", "commands", "acceptance"):
        candidate = dict(metadata)
        del candidate[field]
        bad = (ev.decode()[:match.start(1)] + json.dumps(candidate) + ev.decode()[match.end(1):]).encode()
        reject("evidence omitted " + field, lambda bad=bad: evidence(bad, complete))
    for name, old, new in (("evidence unsupported acceptance", "conditional manual review", "production complete"),
                          ("evidence missing manual gate", GATES[0], "removed"),
                          ("evidence stale hash", metadata["artifacts"][CHECKER], "0" * 64)):
        require(old in ev.decode(), "evidence mutation exercised")
        reject(name, lambda old=old, new=new: evidence(ev.decode().replace(old, new).encode(), complete))
    zero = dict(metadata)
    zero["commands"] = dict(metadata["commands"])
    zero["commands"]["inventory"] = dict(zero["commands"]["inventory"], checks=0)
    bad = (ev.decode()[:match.start(1)] + json.dumps(zero) + ev.decode()[match.end(1):]).encode()
    reject("evidence zero checked mode", lambda: evidence(bad, complete))
    require(load_source() == inputs and (ROOT / DECISIONS).read_bytes() == register
            and (ROOT / SCOPE).read_bytes() == scope_bytes, "canonical bytes untouched")

    require(rejected > 0, "positive rejection count")
    print(f"PASS self-check: {rejected} asserted rejections; valid source/scope/inventory/decisions/all/evidence and pending controls passed")

def dispatch(mode):
    if mode == "all":
        for name, count in all_contracts(load_all()).items():
            print(f"PASS {name}: {count} executed checks (local documentation only)")
    elif mode == "source":
        print(f"PASS source: {source(load_source())} executed checks (local documentation only)")
    elif mode == "scope":
        print(f"PASS scope: {scope((ROOT / SCOPE).read_bytes())} executed checks (local documentation only)")
    elif mode == "decisions":
        print(f"PASS decisions: {decisions((ROOT / DECISIONS).read_bytes(), load_source())} executed checks; 12 decision rows")
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
    except (ContractError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL T01: {exc}", file=sys.stderr)
        sys.exit(1)
