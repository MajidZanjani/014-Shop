#!/usr/bin/env python3
"""Qualify complete hash-locked Python environments without global packages."""
import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / 'backend/requirements'
PYTHON_VERSION = '3.13.16'
PIP_VERSION = '26.2.1'
DIRECT = {
    'runtime': {'pip': PIP_VERSION, 'django': '5.2.18', 'gunicorn': '26.2.0', 'psycopg': '3.3.6'},
    'tools': {'pip': PIP_VERSION, 'pip-tools': '7.6.2', 'jsonschema': '4.26.0', 'cyclonedx-bom': '7.5.0'},
}

class QualificationError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise QualificationError(message)

def canonical(name):
    return re.sub(r'[-_.]+', '-', name).lower()

def read_lock(path):
    """Validate a deliberately narrow lock syntax; pip owns dependency resolution."""
    records = {}
    pending = ''
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line == '--only-binary :all:':
            require(not pending, 'lock option within requirement')
            continue
        pending += ' ' + line.removesuffix('\\').strip()
        if line.endswith('\\'):
            continue
        match = re.fullmatch(r'\s*([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([A-Za-z0-9_.+!-]+)((?:\s+--hash=sha256:[0-9a-f]{64})+)\s*', pending)
        require(match is not None, 'missing hash or unsupported/unpinned lock requirement')
        name = canonical(match[1])
        require(name not in records, 'duplicate lock distribution')
        records[name] = {'version': match[2], 'hashes': re.findall(r'--hash=sha256:([0-9a-f]{64})', match[3])}
        pending = ''
    require(not pending, 'unfinished lock continuation')
    require(bool(records), 'empty lock inventory')
    return records

def validate_environment(data, expected, direct):
    require(isinstance(data, dict), 'environment object required')
    require(data.get('python') == PYTHON_VERSION, 'interpreter identity mismatch')
    require(data.get('platform') == 'linux' and data.get('machine') == 'x86_64', 'target must be Linux x86_64')
    require(data.get('isolated') is True and data.get('user_site') is False, 'environment must exclude global/user site packages')
    actual = data.get('distributions')
    require(isinstance(actual, dict) and bool(actual), 'empty installed inventory')
    require(set(actual) == set(expected), 'missing or unexpected installed dependency')
    for name, version in actual.items():
        require(version == expected[name]['version'], 'installed distribution identity mismatch: ' + name)
    for name, version in direct.items():
        require(actual.get(name) == version, 'tool/runtime identity mismatch: ' + name)
    return len(actual) + 5 + len(direct)

def clean_environment(scratch):
    env = {name: os.environ[name] for name in ('PATH', 'LANG', 'SSL_CERT_FILE', 'NIX_SSL_CERT_FILE') if name in os.environ}
    env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PIP_CONFIG_FILE=os.devnull,
               PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_INPUT='1',
               PIP_CACHE_DIR=str(scratch / 'pip-cache'), TMPDIR=str(scratch / 'tmp'))
    (scratch / 'tmp').mkdir(exist_ok=True)
    return env

def run(command, *, env, timeout=180):
    result = subprocess.run([str(item) for item in command], cwd=ROOT, env=env, timeout=timeout,
                            capture_output=True, text=True)
    require(result.returncode == 0, 'command failed: ' + str(command[0]) + '\n' + (result.stdout + result.stderr)[-8000:])
    return result.stdout

def tool_identity(env):
    require(platform.python_version() == PYTHON_VERSION and sys.platform == 'linux'
            and platform.machine() == 'x86_64', 'use the pinned Linux Python development shell')
    require(str(Path(sys.executable).resolve()).startswith('/nix/store/'), 'interpreter must come from pinned Nix tools')
    pip = run([sys.executable, '-I', '-m', 'pip', '--version'], env=env)
    require(pip.startswith('pip ' + PIP_VERSION + ' '), 'pinned installer identity mismatch')
    postgres = shutil.which('postgres', path=env['PATH'])
    require(postgres is not None and str(Path(postgres).resolve()).startswith('/nix/store/'), 'pinned PostgreSQL unavailable')
    version = run([postgres, '--version'], env=env).strip()
    require(version == 'postgres (PostgreSQL) 18.6', 'PostgreSQL build version mismatch')
    package = Path(postgres).resolve().parent.parent
    references = run(['nix-store', '-q', '--references', package], env=env).splitlines()
    require(len(references) < 100 and all(ref.startswith('/nix/store/') for ref in references), 'bounded pinned store references required')
    candidates = {Path(ref) / 'lib' for ref in [str(package), *references] if (Path(ref) / 'lib/libpq.so').is_file()}
    require(len(candidates) == 1, 'unique pinned libpq library unavailable')
    library = candidates.pop()
    return library

@contextlib.contextmanager
def frozen_environment(kind, scratch):
    """Install only locked wheels into an owned new venv, then yield it and its env."""
    require(kind in DIRECT, 'unknown environment kind')
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=False)
    env = clean_environment(scratch)
    library = tool_identity(env)
    env['LD_LIBRARY_PATH'] = str(library)
    env['PSYCOPG_IMPL'] = 'python'
    lock = REQUIREMENTS / (kind + '-linux-py313.txt')
    expected = read_lock(lock)
    for name, version in DIRECT[kind].items():
        require(name in expected and expected[name]['version'] == version, 'direct reviewed version differs: ' + name)
    wheels = scratch / 'wheels'
    run([sys.executable, '-I', '-m', 'pip', 'download', '--index-url', 'https://pypi.org/simple',
         '--only-binary=:all:', '--require-hashes', '--dest', wheels, '-r', lock], env=env)
    require(wheels.is_dir() and len(list(wheels.glob('*.whl'))) == len(expected), 'incomplete wheel inventory')
    for wheel in wheels.iterdir():
        require(wheel.suffix == '.whl' and wheel.is_file(), 'only inert wheels may be installed')
        require(hashlib.sha256(wheel.read_bytes()).hexdigest() in {h for item in expected.values() for h in item['hashes']}, 'wheel not in verified lock')
    venv = scratch / 'venv'
    run([sys.executable, '-I', '-m', 'venv', '--without-pip', venv], env=env, timeout=30)
    python = venv / 'bin/python3'
    run([sys.executable, '-I', '-m', 'pip', '--python', python, 'install', '--no-index',
         '--find-links', wheels, '--only-binary=:all:', '--require-hashes', '-r', lock], env=env)
    try:
        yield python, env, expected
    finally:
        # TemporaryDirectory's caller owns cleanup. Never reset an existing/global environment.
        pass

def inspect_environment(python, env, kind):
    imports = ['django', 'gunicorn', 'psycopg'] if kind == 'runtime' else ['piptools', 'jsonschema', 'cyclonedx_py', 'lxml.etree', 'rpds']
    source = '''import importlib, importlib.metadata as md, json, platform, site, sys
for module in MODULES: importlib.import_module(module)
values = {}
for dist in md.distributions():
    name = dist.metadata['Name'].lower().replace('_', '-').replace('.', '-')
    if name in values: raise RuntimeError('duplicate installed distribution')
    values[name] = dist.version
value = {'python': platform.python_version(), 'platform': sys.platform, 'machine': platform.machine(),
         'isolated': sys.prefix != sys.base_prefix and not any(p.startswith(sys.base_prefix + '/lib/python') and p.endswith('site-packages') for p in sys.path),
         'user_site': site.ENABLE_USER_SITE, 'distributions': values}
if 'psycopg' in MODULES:
    from psycopg import pq
    if pq.version() != 180006 or pq.__impl__ != 'python': raise RuntimeError('libpq identity mismatch')
    value['libpq'] = pq.version()
print(json.dumps(value))
'''.replace('MODULES', repr(imports))
    return json.loads(run([python, '-I', '-c', source], env=env))

def qualify():
    start = time.monotonic()
    owned = ROOT / '.scratch'
    owned.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='python-qualify-', dir=owned) as directory:
        scratch = Path(directory)
        total = 0
        for kind in DIRECT:
            with frozen_environment(kind, scratch / kind) as (python, env, expected):
                run([python, '-I', '-m', 'pip', 'check'], env=env, timeout=30)
                data = inspect_environment(python, env, kind)
                checks = validate_environment(data, expected, DIRECT[kind])
                total += checks
                print(json.dumps({'environment': kind, 'distributions': data['distributions'], 'libpq': data.get('libpq'), 'checks': checks}))
        import unittest
        suite = unittest.TestLoader().discover(str(ROOT / 'tests'), pattern='test_python_environment.py')
        test_count = suite.countTestCases()
        require(test_count >= 5, 'missing negative-control tests')
        output = io.StringIO()
        result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
        require(result.wasSuccessful() and result.testsRun == test_count and not result.skipped,
                'negative-control tests failed or skipped: ' + output.getvalue())
        print(f'PYTHON_ENVIRONMENT_PASS checks={total} tests={test_count} duration_seconds={time.monotonic()-start:.3f}')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualify', action='store_true', required=True)
    parser.parse_args()
    qualify()

if __name__ == '__main__':
    try:
        main()
    except (QualificationError, OSError, subprocess.TimeoutExpired, ValueError) as error:
        print('PYTHON_ENVIRONMENT_FAIL: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
