#!/usr/bin/env python3
"""Check live planning views against roadmap, canonical state and retained plans."""
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]



def check_activity_views(roadmap,phase,execution_status):
    summary='CURRENT DEVELOPMENT FOCUS; '+execution_status
    listing=re.search(r'^- \[[x ]\] \*\*Phase '+str(phase)+r':.*$',roadmap,re.M)
    detail=re.search(r'^### Phase '+str(phase)+r':.*?(?=^### Phase |\Z)',roadmap,re.M|re.S)
    progress=re.search(r'^\| '+str(phase)+r'\. [^\n]+$',roadmap,re.M)
    for name,view in (('phase list',listing),('phase detail',detail),('progress row',progress)):
        assert view and summary in view[0],'ROADMAP '+name+' disagrees with current execution status'


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
    # Live reporting indexes must describe the same work, not merely link STATE.
    labels=('Current plan','Execution status','Next implementation task')
    def field(text,label):
        match=re.search(r'^\*\*'+re.escape(label)+r':\*\*\s*(.+)$',text,re.M)
        assert match,'Live status missing '+label
        return match[1].strip()
    plan=re.search(r'^current_plan:\s*["\']?(\d+)',state,re.M)
    assert plan,'STATE missing current_plan'
    plan_id=f'{phase:02d}-{int(plan[1]):02d}'
    assert field(state,'Current plan').startswith(plan_id+' '),'STATE current plan disagrees with frontmatter'
    assert any(path.name==plan_id+'-PLAN.md' for path in (planning/'phases').glob('*/*-PLAN.md')),'Current plan file missing'
    for name in ('ROADMAP.md','PROJECT.md','HANDOFF.md'):
        text=(planning/name).read_text()
        focus=re.search(r'^\*\*Current development focus:\*\*\s*(\d+)\b',text,re.M)
        assert focus and int(focus[1])==phase,name+' development focus disagrees with STATE'
        for label in labels:
            assert field(text,label)==field(state,label),name+' disagrees with STATE: '+label
    check_activity_views(roadmap,phase,field(state,'Execution status'))
    status=re.search(r'^status:\s*(\w+)',state,re.M)[1]
    if status=='paused':
        assert field(state,'Execution status').startswith('paused '),'Paused STATE has contradictory execution status'
        assert re.search(r'^paused_at:\s*\S+',state,re.M),'Paused STATE missing routing timestamp'
        assert machine['next']['command']=='$gsd-resume-work','Paused state.json must route to resume'
    elif status=='in_progress':
        assert field(state,'Execution status').startswith('in progress'),'Active STATE has contradictory execution status'
        assert not re.search(r'^paused_at:\s*\S+',state,re.M),'Active STATE retains paused routing timestamp'
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
