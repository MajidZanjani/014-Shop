#!/usr/bin/env python3
"""Check final-amendment precedence and all active requirement/phase mappings."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'.planning'
AMENDMENT='014-Shop-Board-Support-Amendment-2026-10-26.md'


def planning_artifacts():
    # GSD's process-local execution lock is not a committed planning artifact.
    # Exclude only this exact root-relative name, never a broader lock glob.
    return (path for path in P.rglob('*') if path.is_file()
            and path.relative_to(P).as_posix() not in
            {'PURCHASE-FLOW-RECONCILIATION.json', 'milestone.lock'})


def refresh_inventory():
    current={'PROJECT.md','REQUIREMENTS.md','ROADMAP.md','STATE.md','HANDOFF.md','HANDOFF.json','SOURCES.md','SOURCE-MATRIX.md','REPLAN-VERIFICATION.md','EXECUTION-AMENDMENT-2026-10-22.md','PURCHASE-FLOW-AMENDMENT.md','state.json'}
    files=[]
    for path in sorted(planning_artifacts()):
        name=str(path.relative_to(P))
        if name=='config.json':role='workflow-config'
        elif name in current or path.name.startswith('.continue-here') or name.startswith('research/') or path.name.endswith(('-UI-SPEC.md','-QUALIFICATION-REGISTER.md','-COMPLETION-TRACKER.md')):role='current'
        elif name.startswith('quick/') and path.name.endswith('-PLAN.md') and not path.with_name(path.name.replace('PLAN','SUMMARY')).exists():role='current'
        elif path.name.endswith('-PLAN.md') and name.startswith('phases/02-') and not path.with_name(path.name.replace('PLAN','SUMMARY')).exists():role='retained-infrastructure-plan'
        elif path.name.endswith('-PLAN.md') and name.startswith('phases/') and not path.with_name(path.name.replace('PLAN','SUMMARY')).exists():role='current'
        elif path.name.endswith(('-PROGRESS.md','-CONTEXT.md')):role='current'
        else:role='historical-evidence'
        files.append({'path':str(path.relative_to(ROOT)),'role':role,'disposition':
            'Use final revision2/current routing; retain applicable nonconflicting scope' if role in ('current','retained-infrastructure-plan')
            else 'Retain dated evidence/configuration; historical next-step text is not an execution instruction'})
    (P/'PURCHASE-FLOW-RECONCILIATION.json').write_text(json.dumps({'schema':1,'amendment':AMENDMENT,'revision':2,'files':files},indent=2)+'\n')


def main():
    expected='01cc63210f2202462b76108196c55a0f483d56c7f20e5134832b109724571c41'
    assert hashlib.sha256((ROOT/AMENDMENT).read_bytes()).hexdigest()==expected,'amendment bytes changed'
    baseline={'SLL-xSPI-MC-Shop-Proposal-2026-10-21.md':'26a7359624ea4a9625005b39a3fa43beff01c31c830e3b6f122c1ad7417787d0',
        'SLL-xSPI-MC-Shop-Codex-Handoff-2026-10-21.md':'3ff0ecffe4432514bab4a29d500fff05c5537a79c0a8fa494faeb8dfda1c6fac',
        'docs/product-source/SLL_xSPI_MC_Product_Page.md':'562dc4015c62f165df5df3e9ae1aab26b8102385d9dc76a556d5965ddc1a0263'}
    for name,digest in baseline.items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    requirements=(P/'REQUIREMENTS.md').read_text();roadmap=(P/'ROADMAP.md').read_text()
    ids=re.findall(r'^- \[[x ]\] \*\*([A-Z]+-\d+)\*\*:',requirements,re.M)
    assert len(ids)==89 and len(set(ids))==89,'expected80 baseline plus9 amendment requirements'
    mappings=re.findall(r'^\| ([A-Z]+-\d+) \| Phase (\d+) \|',requirements,re.M)
    assert len(mappings)==len(ids) and {i for i,n in mappings}==set(ids),'traceability missing/duplicate'
    phases={n:body for n,body in re.findall(r'### Phase (\d+):([^\n]+[\s\S]*?)(?=\n### Phase |\n## Progress|\Z)',roadmap)}
    assert len(phases)==14
    for identity,number in mappings:
        assert identity in phases[number],identity+' missing from primary phase'
    for path in ('PROJECT.md','ROADMAP.md','SOURCES.md','SOURCE-MATRIX.md','STATE.md','HANDOFF.md'):
        assert 'PURCHASE-FLOW-AMENDMENT.md' in (P/path).read_text(),path+' missing current precedence'
    assert 'Current purchase-flow authority' in (ROOT/'AGENTS.md').read_text()
    assert AMENDMENT in (ROOT/'README.md').read_text()
    focus=re.search(r'^current_phase: [\"\']?(\d+)',(P/'STATE.md').read_text(),re.M)
    assert focus and focus[1].lstrip('0') in phases,'current phase missing from amended roadmap'
    assert 'planned records11/24' not in roadmap,'stale roadmap count'
    # Every existing planning artifact is classified, including historical quick/evidence files.
    inventory=json.loads((P/'PURCHASE-FLOW-RECONCILIATION.json').read_text())
    paths={item['path'] for item in inventory['files']}
    actual={str(p.relative_to(ROOT)) for p in planning_artifacts()}
    assert paths==actual,'planning inventory missing or stale paths'
    for item in inventory['files']:
        assert item['role'] in ('current','historical-evidence','retained-infrastructure-plan','workflow-config')
    print('PURCHASE_PLAN_PASS requirements=89 phases=14 planning_files='+str(len(paths))+' immutable_sources=4')

if __name__=='__main__':
    if sys.argv[1:]==['--refresh-inventory']:refresh_inventory()
    elif sys.argv[1:]:raise SystemExit('usage: check_purchase_plan.py [--refresh-inventory]')
    main()
