"""Owned, disposable PostgreSQL. Never discovers or connects to host clusters."""
from contextlib import contextmanager
import os
from pathlib import Path
import pwd
import secrets
import shutil
import signal
import subprocess
import tempfile

SCRATCH_PARENT = Path("/tmp").resolve()

def run(argv, *, timeout=30, **kwargs):
    process = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True, **kwargs)
    try:
        output, error = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        output, error = process.communicate(timeout=5)
        raise subprocess.TimeoutExpired(argv, timeout, output=output, stderr=error) from None
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, argv, output, error)
    return subprocess.CompletedProcess(argv, process.returncode, output, error)


def validate_root(root, token):
    root = Path(root)
    if (root.is_symlink() or root.parent != SCRATCH_PARENT
            or not root.name.startswith("shop-pg-") or not root.is_dir()
            or any((root / child).is_symlink() for child in ("data", "socket"))
            or not (root / "owned").is_file()
            or (root / "owned").is_symlink()
            or (root / "owned").read_text() != token):
        raise ValueError("unsafe PostgreSQL cleanup root")
    return root


class Cluster:
    def __init__(self, root, token, binaries, prefix):
        self.root, self.token, self.binaries, self.prefix = root, token, binaries, prefix
        self.socket = root / "socket"

    def command(self, tool, *args, timeout=30):
        validate_root(self.root, self.token)
        # Discard ambient libpq connection/service configuration entirely.
        env = {"PATH": os.defpath, "LANG": "C", "HOME": str(self.root),
               "PGPASSFILE": str(self.root / "absent.pgpass"),
               "PGSERVICEFILE": str(self.root / "absent.pg_service.conf"),
               "PGSYSCONFDIR": str(self.root)}
        return run([*self.prefix, str(self.binaries / tool), *map(str, args)],
                   timeout=timeout, env=env)

    def sql(self, statement, database="postgres"):
        return self.command("psql", "-X", "--no-password", "-h", self.socket,
                            "-U", "shop_test", "-d", database, "-At",
                            "-v", "ON_ERROR_STOP=1", "-c", statement).stdout.strip()

    def create_database(self):
        name = "test_" + secrets.token_hex(12)
        self.sql(f'CREATE DATABASE "{name}"')
        return {"HOST": str(self.socket), "PORT": "5432", "NAME": name,
                "USER": "shop_test", "PASSWORD": ""}


@contextmanager
def isolated_postgres():
    directory = os.environ.get("SHOP_POSTGRES_BIN")
    if not directory:
        raise RuntimeError("missing pinned SHOP_POSTGRES_BIN; use nix develop")
    binaries = Path(directory).resolve()
    if not Path(directory).is_absolute() or not str(binaries).startswith("/nix/store/"):
        raise RuntimeError("unexpected PostgreSQL binary provenance")
    for tool in ("initdb", "pg_ctl", "psql", "postgres"):
        if not (binaries / tool).is_file():
            raise RuntimeError("missing PostgreSQL tool: " + tool)
    version = run([str(binaries / "postgres"), "--version"], timeout=10).stdout.strip()
    if version != "postgres (PostgreSQL) 18.6":
        raise RuntimeError("unexpected PostgreSQL server identity: " + version)
    prefix = []
    identity = None
    if os.geteuid() == 0:
        try:
            identity = pwd.getpwnam("claude")  # existing development identity only
        except KeyError:
            raise RuntimeError("run as an unprivileged user; existing claude identity unavailable") from None
        runner = shutil.which("runuser")
        if not runner or identity.pw_uid == 0:
            raise RuntimeError("root requires existing unprivileged claude/runuser")
        prefix = [runner, "--preserve-environment", "-u", identity.pw_name, "--"]
    # nix develop may give root a mode-0700 TMPDIR that an existing test UID
    # cannot traverse. Own a direct /tmp child; never change the shell's parent.
    root = Path(tempfile.mkdtemp(prefix="shop-pg-", dir=SCRATCH_PARENT)).resolve()
    token = secrets.token_hex(32)
    (root / "owned").write_text(token)
    (root / "socket").mkdir(mode=0o700)
    if identity:
        for path in (root, root / "owned", root / "socket"):
            os.chown(path, identity.pw_uid, identity.pw_gid)
    cluster = Cluster(root, token, binaries, prefix)
    started = False
    try:
        cluster.command("initdb", "-D", root / "data", "-U", "shop_test",
                        "--auth-local=trust", "--auth-host=reject", "--no-locale")
        # Unix socket only, inside a mode-0700 unique root. No TCP listener.
        cluster.command("pg_ctl", "-D", root / "data", "-l", root / "server.log",
                        "-o", f"-k {cluster.socket} -h ''", "-w", "-t", "15", "start")
        started = True
        yield cluster
    finally:
        validate_root(root, token)
        # A failed start may nevertheless have created a postmaster: stop it too.
        if started or (root / "data/postmaster.pid").exists():
            cluster.command("pg_ctl", "-D", root / "data", "-m", "immediate",
                            "-w", "-t", "15", "stop")
        if (root / "data/postmaster.pid").exists():
            raise RuntimeError("owned PostgreSQL did not stop; scratch retained")
        shutil.rmtree(validate_root(root, token))
