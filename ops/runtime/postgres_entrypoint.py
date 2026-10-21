"""Native PostgreSQL exec with a content-free stdout/stderr diagnostic worker.

No raw line, SQL state, parameter, exception, PID or text is serialized. This
protects only the inherited console streams, not SQL results/private files.
"""
import os
import re
import sys
import time

EVENT=b'{"event":"postgres.diagnostic"}\n'
CLOSED=b'{"event":"postgres.diagnostic_stream_closed"}\n'
FAILED=b'{"event":"postgres.diagnostic_failed"}\n'
STARTUP_FAILED=b'{"event":"postgres.startup_failed"}\n'
CHUNK_SIZE=4096
INTERVAL=1.0


def emit(fd,event):
    if event not in (EVENT,CLOSED,FAILED,STARTUP_FAILED):raise ValueError('closed event required')
    if os.write(fd,event)!=len(event):raise OSError('diagnostic output unavailable')


def filter_stream(source,destination):
    """Bound memory and event rate; discard every source byte, including binary."""
    last=None
    while True:
        chunk=os.read(source,CHUNK_SIZE)
        if not chunk:
            emit(destination,CLOSED)
            return
        now=time.monotonic()
        if last is None or now-last>=INTERVAL:
            emit(destination,EVENT);last=now


def _exec_filtered(argv):
    """Trusted internal argv only. Replaces the caller; does not return."""
    for fd in (0,1,2):os.fstat(fd)
    source,sink=os.pipe2(os.O_CLOEXEC)
    child=os.fork()
    if child==0:
        os.close(sink)
        os.close(0)
        try:
            filter_stream(source,1)
        except BaseException:
            try:emit(1,FAILED)
            except BaseException:pass
            os._exit(1)
        finally:
            os.close(source)
        os._exit(0)
    os.close(source)
    os.dup2(sink,1);os.dup2(sink,2);os.close(sink)
    # No ambient PGDATA/PGPASSWORD, library injection, proxy or secret variables.
    environment={'PATH':os.defpath,'HOME':'/tmp','TMPDIR':'/tmp','LANG':'C','LC_ALL':'C'}
    try:
        os.execve(argv[0],argv,environment)
    except BaseException:
        # Still through the content-free worker; never print exception/argv.
        try:emit(2,STARTUP_FAILED)
        except BaseException:pass
        os._exit(1)


def main():
    argv=sys.argv[1:]
    if (os.geteuid()==0 or not argv or not isinstance(argv[0],str)
        or re.fullmatch(r'/nix/store/[a-z0-9]{32}-[^/]+/bin/postgres',argv[0]) is None
        or not os.path.realpath(argv[0]).startswith('/nix/store/')):
        raise ValueError('explicit nonroot native PostgreSQL required')
    _exec_filtered(argv)

if __name__=='__main__':
    try:main()
    except BaseException:
        try:emit(2,STARTUP_FAILED)
        except BaseException:pass
        raise SystemExit(1) from None
