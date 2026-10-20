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

def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    if mode == "source":
        print(f"PASS source: {source(load_source())} executed checks (local documentation only)")
    else:
        raise ContractError("unimplemented mode: " + mode)

if __name__ == "__main__":
    try:
        main()
    except (ContractError, OSError) as exc:
        print(f"FAIL T01: {exc}", file=sys.stderr)
        sys.exit(1)
