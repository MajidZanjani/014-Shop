"""Evaluated Nix/TOML/shell contract tests, never a Podman invocation."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import check_deployment as check


class RootlessRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        expr='let f = builtins.getFlake "git+file://${toString ./.}?dir=ops/nixos"; in (import ./ops/nixos/tests/shop.nix { inherit (f.inputs) nixpkgs; shopModule = f.nixosModules.shop; }).runtimeCandidate'
        cls.candidate=json.loads(check.run(['nix','eval','--json','--impure','--expr',expr]))

    def test_real_evaluated_configs_and_shell_syntax(self):
        self.assertTrue(check.validate_runtime_contract(self.candidate))

    def test_shared_or_unbounded_storage_denied(self):
        for before,after in [('/srv/shop/containers/storage','/var/lib/containers/storage'),
                             ('/run/user/9909/shop-containers','/run/containers/storage'),
                             ('driver = "overlay"','driver = "vfs"')]:
            value=copy.deepcopy(self.candidate);value['storageText']=value['storageText'].replace(before,after)
            with self.subTest(after=after),self.assertRaises(ValueError):check.validate_runtime_contract(value)

    def test_rootful_or_shared_network_runtime_denied(self):
        for before,after in [('cgroup_manager = "systemd"','cgroup_manager = "cgroupfs"'),
                             ('network_backend = "netavark"','network_backend = "cni"'),
                             ('/srv/shop/containers/networks','/etc/containers/networks'),
                             ('pull_policy = "never"','pull_policy = "always"')]:
            value=copy.deepcopy(self.candidate);value['containersText']=value['containersText'].replace(before,after)
            with self.subTest(after=after),self.assertRaises(ValueError):check.validate_runtime_contract(value)

    def test_root_account_and_mutable_config_denied(self):
        for key,new in [('XDG_RUNTIME_DIR','/run/user/0'),('CONTAINERS_CONF','/etc/containers/containers.conf'),
                        ('XDG_DATA_HOME','/var/lib'),('TMPDIR','/tmp'),('CONTAINER_HOST','ssh://synthetic.invalid')]:
            value=copy.deepcopy(self.candidate);value['environment'][key]=new
            with self.subTest(key=key),self.assertRaises(ValueError):check.validate_runtime_contract(value)

    def test_ambient_overrides_and_unguarded_engine_denied(self):
        for key,before,after in [('podmanText','/bin/env -i ','/bin/env '),
                                 ('generatorText','--user --no-kmsg-log','--no-kmsg-log'),
                                 ('podmanText','--expected /srv/shop/control/expected.json','--skip-guard')]:
            value=copy.deepcopy(self.candidate);value[key]=value[key].replace(before,after)
            with self.subTest(key=key),self.assertRaises(ValueError):check.validate_runtime_contract(value)

    def test_no_global_generator_or_activation_artifact(self):
        self.assertFalse(self.candidate['productionActivation'])
        self.assertEqual([path for path in self.candidate['artifacts'] if not path.startswith('xspi-shop/runtime/')], [self.candidate['managerDropinPath']])
        self.assertTrue(check.validate_generator_discovery(self.candidate))
        self.assertNotIn('systemctl',self.candidate['generatorText'])
        self.assertNotIn('loginctl',self.candidate['generatorText'])
        self.assertIn("QUADLET_UNIT_DIRS=/etc/containers/systemd/users/9909",self.candidate['generatorText'])

    def test_actual_quadlets_have_explicit_bounded_tmpfs(self):
        for name in ('app','worker','postgres','gateway'):
            text=(ROOT/'ops/quadlet'/('shop-'+name+'.container')).read_text()
            self.assertTrue(check.validate_quadlet_storage(text))
            for old,new in [('ReadOnlyTmpfs=false','ReadOnlyTmpfs=true'),('ShmSize=32m','ShmSize=1g'),
                            ('Tmpfs=/tmp:rw,size=32m,mode=1777','Tmpfs=/tmp:rw'),
                            ('ShmSize=32m','ShmSize=32m\nTmpfs=/var/tmp:rw')]:
                with self.subTest(name=name,new=new),self.assertRaises(ValueError):
                    check.validate_quadlet_storage(text.replace(old,new))

    def test_instance_only_generator_discovery(self):
        self.assertTrue(check.validate_generator_discovery(self.candidate))
        for key,value in [('managerDropinPath','systemd/system/user@.service.d/50-shop-generators.conf'),
                          ('managerDropinPath','systemd/system/user@1.service.d/50-shop-generators.conf'),
                          ('generatorBundle','/srv/shop/generators'),
                          ('generatorBundle',self.candidate['generatorBundle']+':')]:
            candidate=copy.deepcopy(self.candidate);candidate[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):check.validate_generator_discovery(candidate)

    def test_manager_dropin_cannot_reload_or_expand_search(self):
        original=self.candidate['managerDropinText']
        bundle=self.candidate['generatorBundle']
        for replacement in (original.replace(bundle,bundle+':'),original.replace(bundle,'/etc/systemd/user-generators'),
                            original+'ExecStart=/unapproved\n',original+'[Unit]\nBefore=unrelated.service\n',
                            original+'Environment=SYSTEMD_GENERATOR_PATH=/tmp\n',
                            original+'[DEFAULT]\nOther=unapproved\n'):
            candidate=copy.deepcopy(self.candidate);candidate['managerDropinText']=replacement
            with self.subTest(replacement=replacement),self.assertRaises(ValueError):check.validate_generator_discovery(candidate)
