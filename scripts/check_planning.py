#!/usr/bin/env python3
"""Check live planning views against roadmap, canonical state and retained plans."""
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]


def check(root=ROOT):
    planning=root/'.planning'
    state=(planning/'STATE.md').read_text()
    roadmap=(planning/'ROADMAP.md').read_text()
    machine=json.loads((planning/'state.json').read_text())
    phase=int(re.search(r'^current_phase:\s*["\']?(\d+)',state,re.M)[1])
    current=re.search(r'\*\*Current development focus:\*\*\s*(\d+)',roadmap)
    assert current and int(current[1])==phase,'ROADMAP development focus disagrees with STATE'
    rows={}
    for number,counts,status in re.findall(r'^\| (\d+)\. [^|]+\| ([^|]+)\| ([^|]+)\|[^\n]*$',roadmap,re.M):
        status=status.strip().lower()
        rows[number]='complete' if status.startswith('complete') else 'in_progress' if status.startswith('in progress') else 'pending'
    assert rows and rows.get(str(phase))=='in_progress','Development-focus phase must be In Progress'
    last=re.search(r'\*\*Last fully completed phase:\*\*\s*(\d+)',roadmap)
    assert last and rows.get(last[1])=='complete','Last completed phase must actually be Complete'
    for label,number in [('Current development focus',phase),('Last fully completed phase',int(last[1]))]:
        assert re.search(r'\*\*'+label+r':\*\*\s*'+str(number)+r'\b',state),'STATE missing explicit focus/completion label'
    assert {str(row['number']):row['status'] for row in machine['phases']}==rows,'state.json phase statuses disagree with ROADMAP'
    handoff=planning/'HANDOFF.md'
    if handoff.exists():
        recorded=re.search(r'^\*\*Recorded implementation:\*\*\s*([0-9a-f]{7,40})\s*$',handoff.read_text(),re.M)
        state_head=re.search(r'^state_head:\s*([0-9a-f]{7,40})\s*$',state,re.M)
        assert recorded and state_head and recorded[1]==state_head[1],'HANDOFF recorded implementation disagrees with STATE'
    phases=planning/'phases'
    plans=list(phases.glob('*/*-PLAN.md'));summaries=list(phases.glob('*/*-SUMMARY.md'))
    completed=sum(value=='complete' for value in rows.values())
    expected={'total_phases':len(rows),'completed_phases':completed,'total_plans':len(plans),
              'completed_plans':len(summaries),'percent':round(100*completed/len(rows))}
    for key,value in expected.items():
        match=re.search(r'^  '+key+r':\s*(\d+)\s*$',state,re.M)
        assert match and int(match[1])==value,'STATE count mismatch: '+key
    checked=len(re.findall(r'^- \[x\] \*\*Phase \d+:',roadmap,re.M))
    assert checked==completed,'Roadmap checkboxes disagree with completion table'
    for path in [planning/'PROJECT.md',planning/'REQUIREMENTS.md',planning/'ACTIVITY-LOG.md']:
        text=path.read_text()
        assert 'STATE.md' in text and 'ROADMAP.md' in text,'Live index missing status references: '+path.name
    print(f'PLANNING_PASS phases={len(rows)} development_focus={phase} last_completed_phase={last[1]} completed_phases={completed} plans={len(summaries)}/{len(plans)} files_scanned={sum(1 for p in planning.rglob("*") if p.is_file())}')


if __name__=='__main__':
    try:check()
    except (AssertionError,KeyError,ValueError,TypeError) as error:
        print('PLANNING_FAIL: '+str(error),file=sys.stderr);sys.exit(1)
