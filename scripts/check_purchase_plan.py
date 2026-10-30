#!/usr/bin/env python3
"""Validate SHB scope, every planning disposition and exact historical custody."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / '.planning'
AMENDMENT = '014-Shop-SHB-Proposal-Revision-2026-10-30.md'
DIGEST = 'ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e'
ARCHIVE = ROOT / 'docs/archive/2026-10-30-before-shb'


def planning_artifacts():
    # The process lock is runtime state; exclude inventory itself to avoid a
    # circular hash. Nested similarly named files are still inventoried.
    return (path for path in P.rglob('*') if path.is_file()
            and path.relative_to(P).as_posix() not in
            {'PURCHASE-FLOW-RECONCILIATION.json', 'milestone.lock'})


def role_for(path):
    name = path.relative_to(P).as_posix()
    if name == 'config.json': return 'workflow-config'
    content = path.read_text()
    if 'deferred-IP-or-time-accounting-evidence' in content or re.search(r'^status: superseded$', content, re.M):
        return 'deferred'
    if name.startswith('quick/') and '261030-dsk' not in name:
        return 'historical-evidence'
    if 'retained historical record' in content or '"disposition": "historical-evidence"' in content:
        return 'historical-evidence'
    if name.startswith('phases/02-') and path.name.endswith('-PLAN.md'):
        return 'retained-infrastructure-plan'
    return 'current'


def refresh_inventory():
    files = []
    for path in sorted(planning_artifacts()):
        role = role_for(path)
        files.append({'path':str(path.relative_to(ROOT)), 'role':role,
                      'release':'shb-1.1', 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                      'disposition':'Execute only current SHB routing; retain applicable shared controls' if role in ('current','retained-infrastructure-plan')
                      else 'Preserve exact original evidence/configuration; no historical next action or deferred launch gate'})
    (P/'PURCHASE-FLOW-RECONCILIATION.json').write_text(json.dumps({
        'schema':2, 'amendment':AMENDMENT, 'revision':'1.1', 'source_sha256':DIGEST,
        'archive_manifest':str((ARCHIVE/'manifest.json').relative_to(ROOT)),
        'runtime_exclusions':['.planning/milestone.lock'], 'files':files},indent=2)+'\n')


def check_archive(root=ROOT, archive=ARCHIVE):
    manifest = json.loads((archive/'manifest.json').read_text())
    assert manifest['source'] == AMENDMENT and manifest['revision'] == '1.1'
    paths = [entry['path'] for entry in manifest['files']]
    assert paths and len(paths) == len(set(paths)), 'duplicate/empty original archive'
    for entry in manifest['files']:
        relative = Path(entry['path'])
        assert not relative.is_absolute() and '..' not in relative.parts, 'archive path escape'
        original = archive / relative
        assert original.is_file() and not original.is_symlink(), 'original absent/linked: '+str(relative)
        raw = original.read_bytes()
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256'], 'original evidence changed: '+str(relative)
        current = root / relative
        assert not current.exists() or hashlib.sha256(current.read_bytes()).hexdigest() != entry['sha256'], 'old planning not rewritten: '+str(relative)
    return len(paths)


def main():
    assert hashlib.sha256((ROOT/AMENDMENT).read_bytes()).hexdigest() == DIGEST, 'SHB source changed'
    baseline={'SLL-xSPI-MC-Shop-Proposal-2026-10-21.md':'26a7359624ea4a9625005b39a3fa43beff01c31c830e3b6f122c1ad7417787d0',
              'SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md':'3ff0ecffe4432514bab4a29d500fff05c5537a79c0a8fa494faeb8dfda1c6fac',
              '014-Shop-Board-Support-Amendment-2026-10-26.md':'01cc63210f2202462b76108196c55a0f483d56c7f20e5134832b109724571c41',
              'docs/product-source/SLL_xSPI_MC_Product_Page.md':'562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263'}
    for name,digest in baseline.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    requirements=(P/'REQUIREMENTS.md').read_text();roadmap=(P/'ROADMAP.md').read_text()
    ids=re.findall(r'^- \[[x ]\] \*\*(SHB-\d+)\*\*:',requirements,re.M)
    assert len(ids)==30 and set(ids)=={f'SHB-{i:02d}' for i in range(1,31)}, 'all thirty SHB criteria required'
    mappings=re.findall(r'^\| (SHB-\d+) \| Phase (\d+) \|',requirements,re.M)
    assert len(mappings)==30 and {i for i,_ in mappings}==set(ids), 'missing/duplicate SHB traceability'
    phases={n:body for n,body in re.findall(r'### Phase (\d+):([^\n]+[\s\S]*?)(?=\n### Phase |\n## Progress|\Z)',roadmap)}
    assert len(phases)==14, 'stable T01–T14 structure required'
    for identity,number in mappings: assert identity in phases[number], identity+' missing from phase'
    legacy=re.findall(r'^\| ((?!SHB)[A-Z]+-\d+) \| (.*?) \|',requirements,re.M)
    assert len(legacy)==89 and len({i for i,_ in legacy})==89, 'all previous requirement dispositions required'
    assert all('Deferred' in result for identity,result in legacy if identity in ('FUL-04','FUL-05','FUL-06','OPS-04')), 'dedicated time-ledger requirements must be deferred'
    for name in ('PROJECT.md','ROADMAP.md','SOURCES.md','SOURCE-MATRIX.md','STATE.md','HANDOFF.md'):
        assert AMENDMENT in (P/name).read_text(), name+' missing current source'
    assert 'SHB revision 1.1' in (ROOT/'AGENTS.md').read_text()
    assert AMENDMENT in (ROOT/'README.md').read_text()
    original_count=check_archive()
    inventory=json.loads((P/'PURCHASE-FLOW-RECONCILIATION.json').read_text())
    assert inventory['revision']=='1.1' and inventory['source_sha256']==DIGEST
    paths=[item['path'] for item in inventory['files']]
    actual={str(path.relative_to(ROOT)) for path in planning_artifacts()}
    assert len(paths)==len(set(paths)) and set(paths)==actual, 'missing/stale planning inventory'
    for item in inventory['files']:
        assert item['role'] in ('current','historical-evidence','retained-infrastructure-plan','workflow-config','deferred')
        path=ROOT/item['path']
        assert item['release']=='shb-1.1' and item['role']==role_for(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'], 'stale planning hash: '+item['path']
    print(f'PURCHASE_PLAN_PASS release=shb-1.1 requirements=30 prior_dispositions=89 phases=14 planning_files={len(paths)} archived_originals={original_count} immutable_sources=5')


if __name__=='__main__':
    if sys.argv[1:]==['--refresh-inventory']: refresh_inventory()
    elif sys.argv[1:]: raise SystemExit('usage: check_purchase_plan.py [--refresh-inventory]')
    main()
