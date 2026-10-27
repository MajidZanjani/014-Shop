"""The inherited local controller cannot select arbitrary staff, scope or commands."""
import json
from pathlib import Path
import socket
import sys
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_browser_access import CONTROL_ACTIONS,serve_controls,validate_control_request


class BrowserControlTests(unittest.TestCase):
    def test_exact_sequence_only(self):
        for sequence in range(6):
            value={'index':sequence//3,'action':CONTROL_ACTIONS[sequence%3]}
            self.assertEqual(validate_control_request(json.dumps(value).encode(),sequence),
                             (value['index'],value['action']))
            for changed in ({'index':True},{'index':2},{'index':-1},{'action':'reset'},
                            {'username':'other'},{'checkout':'other'}):
                with self.subTest(sequence=sequence,changed=changed),self.assertRaises(ValueError):
                    validate_control_request(json.dumps(value|changed).encode(),sequence)
        for raw in (b'null',b'[]',b'{}',b'\xff',b'{',b' '*129,b'{"index":1,"index":0,"action":"revoke-support"}'):
            with self.assertRaises(ValueError):validate_control_request(raw,0)
        with self.assertRaises(ValueError):validate_control_request(b'{}',6)

    def test_order_replay_and_failed_effect_are_not_retried(self):
        raw=b'{"index":0,"action":"revoke-support"}\n'
        for operation in ('replay','failed'):
            parent,child=socket.socketpair();child.settimeout(2)
            calls=[];errors=[]
            def perform(index,action):
                calls.append((index,action))
                if operation=='failed':raise ValueError('private failure')
            worker=threading.Thread(target=serve_controls,args=(parent,perform,errors));worker.start()
            try:
                child.sendall(raw)
                if operation=='replay':
                    self.assertEqual(child.recv(128),b'{"ok":true}\n')
                    child.sendall(raw)
                self.assertEqual(child.recv(128),b'')
                worker.join(2)
                self.assertFalse(worker.is_alive())
                self.assertEqual(calls,[(0,'revoke-support')])
                self.assertEqual(errors,['browser control failed'])
            finally:child.close();parent.close()

    def test_fragmentation_and_complete_closed_sequence(self):
        parent,child=socket.socketpair();child.settimeout(2)
        calls=[];errors=[]
        worker=threading.Thread(target=serve_controls,args=(parent,lambda *args:calls.append(args),errors));worker.start()
        try:
            for sequence in range(6):
                raw=json.dumps({'index':sequence//3,'action':CONTROL_ACTIONS[sequence%3]}).encode()+b'\n'
                child.sendall(raw[:3]);child.sendall(raw[3:])
                self.assertEqual(child.recv(128),b'{"ok":true}\n')
            child.shutdown(socket.SHUT_WR);worker.join(2)
            self.assertFalse(worker.is_alive());self.assertEqual(errors,[]);self.assertEqual(len(calls),6)
        finally:child.close();parent.close()


if __name__=='__main__':unittest.main()
