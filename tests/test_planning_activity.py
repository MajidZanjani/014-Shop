"""Reject the actual drift where active roadmap views retained a historical pause."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('planning_activity',ROOT/'scripts/check_planning.py')
planning=importlib.util.module_from_spec(spec);spec.loader.exec_module(planning)

class PlanningActivityTests(unittest.TestCase):
    def setUp(self):
        self.roadmap=(ROOT/'.planning/ROADMAP.md').read_text()
        state=(ROOT/'.planning/STATE.md').read_text()
        self.phase=int(re.search(r'^current_phase:\s*(\d+)',state,re.M)[1])
        self.status=re.search(r'^\*\*Execution status:\*\* (.+)$',state,re.M)[1]
        self.summary='CURRENT DEVELOPMENT FOCUS; '+self.status

    def test_current_views_match(self):
        planning.check_activity_views(self.roadmap,self.phase,self.status)

    def test_each_historical_pause_is_rejected_independently(self):
        patterns=(r'^- \[[x ]\] \*\*Phase '+str(self.phase)+r':.*$',
                  r'^### Phase '+str(self.phase)+r':.*?(?=^### Phase |\Z)',
                  r'^\| '+str(self.phase)+r'\. [^\n]+$')
        for pattern in patterns:
            with self.subTest(pattern=pattern):
                match=re.search(pattern,self.roadmap,re.M|re.S if pattern.startswith('^###') else re.M)
                self.assertIsNotNone(match)
                stale=match[0].replace(self.summary,'CURRENT DEVELOPMENT FOCUS; PAUSED at user request; old counts')
                changed=self.roadmap[:match.start()]+stale+self.roadmap[match.end():]
                with self.assertRaises(AssertionError):planning.check_activity_views(changed,self.phase,self.status)

    def test_explicit_pause_is_valid_when_all_views_agree(self):
        paused='paused — explicit user checkpoint; actual acceptance pending.'
        roadmap=self.roadmap.replace(self.summary,'CURRENT DEVELOPMENT FOCUS; '+paused)
        planning.check_activity_views(roadmap,self.phase,paused)

if __name__=='__main__':unittest.main()
