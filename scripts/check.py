"""Explicit, fail-closed verification lanes. Local/synthetic evidence only."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
QUICK = ("environment", "frontend", "core", "worker", "adapters", "contracts", "boundaries")
DEVELOPMENT = ("frontend", "core-local", "worker-smoke", "adapters", "contracts-local", "catalog")
EXTRA = ("inventory", "locks", "reproducibility", "deployment-profiles",
         "deployment-eval", "postgres-diagnostics", "postgresql-config", "bootstrap-local", "database-destination", "database-tools", "operator-runtime", "native-closure", "native-source-notices", "deployment-build", "deployment-boot")
# (producer, commands, timeout). No optional producers or inferred skips.
LANES = {
    "core-local": ("scripts/check_backend.py", (("python3", "scripts/check_backend.py", "core-local"),), 120),
    "contracts-local": ("scripts/check_contracts.py", (("python3", "scripts/check_contracts.py", "--local"),), 120),
    "catalog": ("scripts/check_catalog.py", (("python3", "scripts/check_catalog.py"),), 120),
    "environment": ("scripts/dev_postgres.py", (), 60),
    "frontend": ("scripts/check_frontend.py", (("python3", "scripts/check_frontend.py"),), 180),
    "core": ("scripts/check_backend.py", (("python3", "scripts/check_backend.py", "core"),), 120),
    "worker-smoke": ("scripts/check_worker.py", (("python3", "scripts/check_worker.py", "worker-smoke"),), 120),
    "worker": ("scripts/check_worker.py", (("python3", "scripts/check_worker.py", "worker"),), 180),
    "adapters": ("backend/shop/adapters/tests.py", (("python3", "scripts/check_backend.py", "adapters"),), 120),
    "contracts": ("scripts/check_contracts.py", (("python3", "scripts/check_contracts.py"),), 120),
    "boundaries": ("scripts/check_boundaries.py", (("python3", "scripts/check_boundaries.py"),), 120),
    "inventory": ("scripts/inventory_artifacts.py", (("python3", "scripts/inventory_artifacts.py"),), 180),
    "locks": ("scripts/check_locks.py", (("python3", "scripts/check_locks.py"),), 900),
    "reproducibility": ("scripts/check_reproducibility.py", (("python3", "scripts/check_reproducibility.py"),), 1800),
    "deployment-profiles": ("scripts/check_deployment.py", (("python3", "scripts/check_deployment.py", "deployment-profiles"),), 300),
    "postgres-diagnostics": ("scripts/check_postgres_diagnostics.py", (("python3", "scripts/check_postgres_diagnostics.py"),), 120),
    "postgresql-config": ("scripts/check_postgresql_config.py", (("python3", "scripts/check_postgresql_config.py"),), 120),
    "bootstrap-local": ("scripts/check_bootstrap.py", (("python3", "scripts/check_bootstrap.py"),), 120),
    "native-source-notices": ("scripts/check_native_source_notices.py", (("python3", "scripts/check_native_source_notices.py"),), 180),
    "native-closure": ("scripts/check_native_closure.py", (("python3", "scripts/check_native_closure.py"),), 180),
    "operator-runtime": ("scripts/check_operator_runtime.py", (("python3", "scripts/check_operator_runtime.py"),), 180),
    "database-tools": ("scripts/check_database_tools.py", (("python3", "scripts/check_database_tools.py"),), 180),
    "database-destination": ("scripts/check_database_destination.py", (("python3", "scripts/check_database_destination.py"),), 120),
    "deployment-eval": ("scripts/check_deployment.py", (("python3", "scripts/check_deployment.py", "deployment-eval"),), 300),
    "deployment-build": ("scripts/check_deployment.py", (("python3", "scripts/check_deployment.py", "deployment-build"),), 3600),
    "deployment-boot": ("scripts/check_deployment.py", (("python3", "scripts/check_deployment.py", "deployment-boot"),), 3600),
}


def required_lanes(mode):
    if mode == "dev":
        return DEVELOPMENT
    if mode == "quick":
        return QUICK
    if mode == "all":
        return QUICK + EXTRA
    if mode not in LANES:
        raise ValueError("unknown lane: " + mode)
    return (mode,)


def positive_counts(output):
    tests = sum(map(int, re.findall(r'(?:Ran |tests["\s:=]+)(\d+)', output)))
    checks = sum(map(int, re.findall(r'checks["\s:=]+(\d+)', output)))
    if tests + checks == 0:
        raise RuntimeError("zero tests/checks; required verification unexecuted")
    if re.search(r"(?:skipped|failures|errors)[=: ]+[1-9]", output, re.I):
        raise RuntimeError("failed/skipped required verification")
    return tests, checks


def tool_version(argv):
    with tempfile.TemporaryDirectory(prefix="shop-tools-") as home:
        env = {"HOME": home, "PATH": os.environ.get("SHOP_TOOL_PATH", os.defpath),
               "LANG": "C", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
               "PIP_CONFIG_FILE": os.devnull,
               "NPM_CONFIG_USERCONFIG": str(Path(home) / "absent.npmrc"),
               "NPM_CONFIG_GLOBALCONFIG": str(Path(home) / "absent-global.npmrc"),
               "NPM_CONFIG_CACHE": str(Path(home) / "cache"),
               "XDG_CONFIG_HOME": home}
        return subprocess.run(argv, cwd=home, env=env, capture_output=True, text=True,
                              timeout=15, check=True)


def tool_identities():
    identities = {}
    for name, key, expected in (("python3", "SHOP_PYTHON", "3.13.16"),
                                 ("node", "SHOP_NODE", "v24.22.0"),
                                 ("npm", "SHOP_NPM", "11.19.1")):
        found = shutil.which(name)
        identities[name] = {"path": found}
        print("TOOL_PROVENANCE " + json.dumps({name: identities[name]}), flush=True)
        pinned = os.environ.get(key)
        if (not found or not pinned or not str(Path(pinned).resolve()).startswith("/nix/store/")
                or Path(found).resolve() != Path(pinned).resolve()):
            raise RuntimeError("unexpected binary identity: " + name)
        result = tool_version([found, "--version"])
        version = result.stdout.strip().removeprefix("Python ")
        if version != expected:
            raise RuntimeError(f"unexpected {name} version: {version}, expected {expected}")
        identities[name]["version"] = version
    return identities


def environment():
    identities = tool_identities()
    pip = tool_version([sys.executable, "-m", "pip", "--version"]).stdout.strip()
    pip_root = str(Path(os.environ["SHOP_PYTHON"]).parent.parent / "lib")
    if not pip.startswith("pip 26.2.1 ") or f"from {pip_root}/" not in pip:
        raise RuntimeError("unexpected pip identity: " + pip)
    identities["pip"] = {"version": pip}
    for tool in ("systemctl", "tar", "xz", "bzip2", "gzip", "unzip", "make", "gcc", "pkg-config"):
        found = shutil.which(tool)
        if not found or not str(Path(found).resolve()).startswith("/nix/store/"):
            raise RuntimeError("missing/unpinned native tool: " + tool)
        identities[tool] = {"path": str(Path(found).resolve())}
    import dev_postgres
    previous_scratch_parent = dev_postgres.SCRATCH_PARENT
    parent = os.environ.get('SHOP_TEST_SCRATCH')
    if parent:
        scratch = Path(parent)
        if scratch.is_symlink() or not scratch.is_dir() or len(str(scratch.resolve())) + 50 >= 108:
            raise RuntimeError("short existing owned SHOP_TEST_SCRATCH required")
        dev_postgres.SCRATCH_PARENT = scratch.resolve()
    isolated_postgres = dev_postgres.isolated_postgres
    try:
        with isolated_postgres() as pg:
            root = pg.root
            row = pg.sql("SELECT pg_backend_pid(), current_setting('server_version'), version()")
            fields = row.split("|")
            if len(fields) != 3 or int(fields[0]) <= 0 or fields[1] != "18.6":
                raise RuntimeError("unexpected PostgreSQL backend: " + row)
            print("POSTGRESQL_BACKEND " + row)
            identities["postgresql"] = {"path": str(pg.binaries), "version": fields[1]}
        if root.exists():
            raise RuntimeError("owned PostgreSQL scratch remains")
    finally:
        dev_postgres.SCRATCH_PARENT = previous_scratch_parent
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_check.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.testsRun == 0 or result.skipped:
        raise RuntimeError("environment tests failed, skipped or empty")
    print("ENVIRONMENT_PASS")
    return result.testsRun, 2, identities


def execute(lane):
    start = time.monotonic()
    producer, commands, timeout = LANES[lane]
    if not (ROOT / producer).is_file():
        raise RuntimeError(f"{lane}: missing required producer {producer}")
    if lane == "environment":
        tests, checks, identities = environment()
    else:
        tests = checks = 0
        identities = {}
        for command in commands:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                    timeout=timeout, check=False)
            output = result.stdout + result.stderr
            print(output, end="")
            if result.returncode:
                raise RuntimeError(f"{lane}: command failed ({result.returncode})")
            marker = lane.upper().replace("-", "_") + "_PASS"
            if marker not in output:
                raise RuntimeError(f"{lane}: missing required marker {marker}")
            t, c = positive_counts(output)
            tests += t
            checks += c
    print(json.dumps({"lane": lane, "checks": checks, "tests": tests,
                      "failures": 0, "elapsed_seconds": time.monotonic() - start,
                      "tool_identity": identities, "evidence_class": "local-synthetic"}))


def main(argv=None):
    provenance = ", ".join(f"{tool}={shutil.which(tool) or 'MISSING'}"
                           for tool in ("python3", "node", "npm", "nix", "psql"))
    parser = argparse.ArgumentParser(description=__doc__, epilog="Tool provenance: " + provenance)
    parser.add_argument("lane", choices=(*LANES, "quick", "all", "dev"))
    args = parser.parse_args(argv)
    lanes = required_lanes(args.lane)
    try:
        # Preflight every producer before executing any aggregate lane.
        for lane in lanes:
            if not (ROOT / LANES[lane][0]).is_file():
                raise RuntimeError(f"{lane}: missing required producer {LANES[lane][0]}")
        if "environment" not in lanes:
            tool_identities()
        for lane in lanes:
            if args.lane == 'dev' and lane == 'frontend':
                original = LANES[lane]
                LANES[lane] = ('scripts/check_frontend_dev.py', (('python3','scripts/check_frontend_dev.py'),), 240)
                try: execute(lane)
                finally: LANES[lane] = original
            else: execute(lane)
        if args.lane == "dev":
            print("LOCAL_DEVELOPMENT_PASS; release qualification pending")
        elif args.lane == "all":
            print("FULL_PASS")
        elif args.lane == "quick":
            print("QUICK_PASS")
        return 0
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL lane={args.lane} failures=1: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
