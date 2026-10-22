#!/usr/bin/env python3
"""Build only reviewed public inputs and reject synthetic privacy/runtime leaks."""
import gzip
import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CANARIES = (b'PRIVATE_HOST_ID_SYNTHETIC_7de1', b'PRIVATE_KEY_SYNTHETIC_48ba',
            b'PRIVATE_BUSINESS_TAX_SYNTHETIC_61fc', b'https://private.invalid/bearer/SYNTHETIC_991a')
LIMIT = 32 * 1024 * 1024

class BoundaryError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise BoundaryError(message)

def manifest(value):
    require(isinstance(value, dict) and set(value) == {'schema_version', 'evidence_class', 'files'}, 'closed build-input manifest required')
    require(value['schema_version'] == 1 and value['evidence_class'] == 'local-synthetic', 'synthetic build manifest required')
    names = value['files']
    require(isinstance(names, list) and 0 < len(names) <= 100 and all(isinstance(name, str) for name in names), 'bounded nonempty input list required')
    require(len(set(names)) == len(names), 'duplicate public input')
    for name in names:
        path = PurePosixPath(name)
        require(bool(name) and bool(path.parts) and path.as_posix() == name and not path.is_absolute() and '..' not in path.parts and '\\' not in name
                and not any(part.startswith('.') or part.lower() in ('private', 'secrets', 'fixtures') for part in path.parts), 'private/unsafe input path')
        require(path.parts[0] in ('src', 'public', 'tests') or name in ('package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json'), 'unexpected build-input family')
    require({'package.json', 'package-lock.json', 'astro.config.mjs', 'tsconfig.json', 'src/pages/index.astro'} <= set(names), 'missing required public build input')
    return names

def copy_inputs(source, destination, names):
    source, destination = Path(source), Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name in names:
        origin = source / name
        require(origin.is_file() and not origin.is_symlink(), 'missing/symlink public input')
        require(origin.resolve().is_relative_to(source.resolve()), 'public input escaped source root')
        require(origin.stat().st_size <= LIMIT, 'oversized public input')
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)

# Use the installed TypeScript parser, not keyword counting, for code imports and
# exported prerender policy. The actual resolved Astro configuration is checked too.
SOURCE_POLICY = r'''
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
const root = process.argv[1];
const require = createRequire(path.join(root, 'package.json'));
const ts = require('typescript');
const names = JSON.parse(fs.readFileSync(path.join(root, 'build-inputs.json'), 'utf8')).files;
const allowed = new Set(names);
for (const name of names.filter(name => /\.(?:ts|tsx|astro)$/.test(name))) {
  const raw = fs.readFileSync(path.join(root, name), 'utf8');
  if (name.endsWith('.astro') && /\bserver:defer\b/.test(raw)) throw Error('server island prohibited');
  const source = name.endsWith('.astro') ? (/^---\n([\s\S]*?)\n---/.exec(raw)?.[1] ?? '') : raw;
  const tree = ts.createSourceFile(name, source, ts.ScriptTarget.Latest, true, name.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
  function visit(node) {
    if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node) && node.moduleSpecifier) {
      const id = node.moduleSpecifier.text;
      if (id.startsWith('.')) {
        const target = path.posix.normalize(path.posix.join(path.posix.dirname(name), id));
        if (![target, target + '.ts', target + '.tsx', target + '.astro'].some(item => allowed.has(item))) throw Error('import outside public allowlist');
      } else if (!['react', 'astro:content', 'astro/loaders', 'astro/zod'].includes(id)) throw Error('unreviewed or runtime module prohibited');
      if (node.importClause?.namedBindings && ts.isNamedImports(node.importClause.namedBindings)) {
        if (node.importClause.namedBindings.elements.some(item => /^(getLiveCollection|getLiveEntry|defineLiveCollection)$/.test((item.propertyName ?? item.name).text))) throw Error('live collection prohibited');
      }
    }
    if (ts.isCallExpression(node)) {
      const exp=node.expression;
      const fetchCall=ts.isIdentifier(exp) && exp.text==='fetch' || ts.isPropertyAccessExpression(exp) && exp.name.text==='fetch';
      if (fetchCall && !(name==='src/lib/customer-api.ts' && ts.isPropertyAccessExpression(exp) && exp.expression.getText(tree)==='window')) throw Error('unreviewed/build-time fetch prohibited');
      if (exp.kind === ts.SyntaxKind.ImportKeyword || ts.isIdentifier(exp) && ['require', 'eval'].includes(exp.text)) throw Error('dynamic/external input prohibited');
    }
    if (ts.isVariableDeclaration(node) && node.name.getText(tree) === 'prerender' && node.initializer?.kind === ts.SyntaxKind.FalseKeyword) throw Error('request-time route prohibited');
    ts.forEachChild(node, visit);
  }
  visit(tree);
}
const { default: config } = await import(pathToFileURL(path.join(root, 'astro.config.mjs')));
if (config.output !== 'static' || config.adapter || config.site !== 'https://shop.xspi.pro' || config.integrations.some(item => item.name !== '@astrojs/react')) throw Error('static runtime configuration violated');
console.log('PUBLIC_SOURCE_POLICY_PASS checks=' + names.length);
'''

def safe_env(scratch):
    env = {name: os.environ[name] for name in ('PATH', 'SSL_CERT_FILE', 'NIX_SSL_CERT_FILE', 'LANG') if name in os.environ}
    temp = scratch / 'tmp'; temp.mkdir(exist_ok=True)
    env.update(ASTRO_TELEMETRY_DISABLED='1', TMPDIR=str(temp),
               NPM_CONFIG_USERCONFIG=str(scratch / 'absent.npmrc'),
               NPM_CONFIG_GLOBALCONFIG=str(scratch / 'absent-global.npmrc'),
               NPM_CONFIG_CACHE=str(scratch / 'npm-cache'),
               XDG_CONFIG_HOME=str(scratch / 'config'), XDG_CACHE_HOME=str(scratch / 'cache'))
    return env

def command(args, cwd, env, timeout=90):
    result = subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, 'frontend command failed: ' + str(args[0]) + '\n' + (result.stdout + result.stderr)[-7000:])
    return result.stdout + result.stderr

def source_policy(project, env):
    return command(['node', '--input-type=module', '--eval', SOURCE_POLICY, project], project, env, 30)

def scan_bytes(name, data, depth=0):
    require(depth <= 3 and len(data) <= LIMIT, 'output/archive inspection limit')
    require(not any(canary in data or base64.b64encode(canary) in data for canary in CANARIES), 'synthetic private canary leaked: ' + name)
    count = 1
    lower = name.lower()
    if lower.endswith('.zip') or data.startswith(b'PK\x03\x04'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            require(len(archive.infolist()) <= 1000 and sum(item.file_size for item in archive.infolist()) <= LIMIT, 'oversized archive')
            for item in archive.infolist():
                if not item.is_dir(): count += scan_bytes(item.filename, archive.read(item), depth + 1)
    elif lower.endswith(('.gz', '.tgz')) or data.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as compressed:
            raw = compressed.read(LIMIT + 1)
        count += scan_bytes(name[:-3] + ('.tar' if lower.endswith('.tgz') else ''), raw, depth + 1)
    elif lower.endswith('.tar') or data[257:262] == b'ustar':
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
            size = 0
            members = archive.getmembers(); require(len(members) <= 1000, 'oversized archive')
            for member in members:
                require(member.isfile() or member.isdir(), 'archive link/device prohibited')
                size += member.size; require(size <= LIMIT, 'oversized archive')
                if member.isfile(): count += scan_bytes(member.name, archive.extractfile(member).read(LIMIT + 1), depth + 1)
    elif lower.endswith(('.br', '.xz', '.bz2')):
        raise BoundaryError('unsupported compressed output must not escape inspection')
    return count

def scan_output(dist):
    dist = Path(dist)
    require(dist.is_dir() and (dist / 'index.html').is_file(), 'missing static output')
    paths = sorted(dist.rglob('*'))
    require(0 < len(paths) <= 1000 and not (dist / 'server').exists(), 'empty/excessive/server output')
    require(sum(path.stat().st_size for path in paths if path.is_file()) <= LIMIT, 'oversized public output')
    inventory = []; count = 0
    for path in paths:
        require(not path.is_symlink(), 'output symlink prohibited')
        if not path.is_file(): continue
        data = path.read_bytes(); count += scan_bytes(str(path.relative_to(dist)), data)
        inventory.append({'path': str(path.relative_to(dist)), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    require(len(inventory) > 1, 'missing public hydration outputs')
    return inventory, count

def main():
    start = time.monotonic(); owned = ROOT / '.scratch'; owned.mkdir(exist_ok=True)
    inputs = json.loads((ROOT / 'frontend/build-inputs.json').read_text()); names = manifest(inputs)
    with tempfile.TemporaryDirectory(prefix='frontend-boundary-', dir=owned) as temporary:
        scratch = Path(temporary); project = scratch / 'frontend'
        copy_inputs(ROOT / 'frontend', project, names)
        (project / 'build-inputs.json').write_text(json.dumps(inputs))
        private = scratch / 'private'; private.mkdir()
        (private / 'synthetic-only.txt').write_bytes(b'\n'.join(CANARIES))
        env = safe_env(scratch)
        command(['npm', 'ci', '--registry=https://registry.npmjs.org', '--no-audit', '--no-fund'], project, env)
        policy = source_policy(project, env)
        require('PUBLIC_SOURCE_POLICY_PASS' in policy, 'source policy did not execute')
        command(['npm', 'run', 'check'], project, env)
        # Only this build process receives an empty network namespace. Existing
        # host/guest interfaces, routes and services are not modified.
        command(['unshare', '--net', '--', 'npm', 'run', 'build'], project, env)
        inventory, count = scan_output(project / 'dist')
        smoke = command(['npm', 'run', 'test'], project, env, 120)
        require('fail 0' in smoke and 'configuration: Altera annual fixed' in smoke, 'required real frontend tests absent')
        os.environ['SHOP_FRONTEND_TEST_ROOT'] = str(project)
        os.environ['SHOP_FRONTEND_TEST_ENV'] = json.dumps(env)
        try:
            suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_frontend_boundary.py')
            test_output = io.StringIO()
            result = unittest.TextTestRunner(stream=test_output, verbosity=2).run(suite)
            require(result.wasSuccessful() and result.testsRun > 0 and not result.skipped, 'boundary cases failed/skipped/empty: ' + test_output.getvalue())
        finally:
            os.environ.pop('SHOP_FRONTEND_TEST_ROOT', None); os.environ.pop('SHOP_FRONTEND_TEST_ENV', None)
        print(json.dumps({'evidence_class': 'local-synthetic', 'artifacts': inventory}))
        print(f'FRONTEND_PASS checks={count + len(names)} tests={result.testsRun + int(__import__('re').search(r'tests (\d+)', smoke).group(1))} duration_seconds={time.monotonic()-start:.3f}')

if __name__ == '__main__':
    try: main()
    except (BoundaryError, OSError, ValueError, subprocess.TimeoutExpired, zipfile.BadZipFile, tarfile.TarError) as error:
        print('FRONTEND_FAIL: ' + str(error), file=sys.stderr); raise SystemExit(1)
