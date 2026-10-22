#!/usr/bin/env python3
"""Candidate evaluation only; image build/runtime/host acceptance remain separate."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]


def run(args,timeout=60):
    return subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout,check=True).stdout



def validate_runtime_contract(candidate):
    """Check evaluated account-scoped config text; not runtime compatibility."""
    if candidate.get('productionActivation') is not False:raise ValueError('candidate runtime cannot activate')
    containers=tomllib.loads(candidate['containersText']);storage=tomllib.loads(candidate['storageText'])
    engine=containers['engine'];network=containers['network'];account=candidate['environment']
    expected_engine={'cgroup_manager','events_logger','runtime','conmon_path','helper_binaries_dir','tmp_dir','volume_path','pull_policy','runtimes'}
    if set(containers)!={'containers','engine','network'} or set(engine)!=expected_engine or set(engine['runtimes'])!={'crun'}:raise ValueError('closed engine config required')
    settings=storage['storage']
    if set(storage)!={'storage'} or set(settings)!={'driver','runroot','graphroot','rootless_storage_path','options'} or set(settings['options'])!={'overlay'} or set(settings['options']['overlay'])!={'mount_program'}:raise ValueError('closed storage config required')
    if set(account)!={'HOME','XDG_RUNTIME_DIR','XDG_CONFIG_HOME','XDG_DATA_HOME','TMPDIR','CONTAINERS_CONF','CONTAINERS_STORAGE_CONF','CONTAINERS_REGISTRIES_CONF','DBUS_SESSION_BUS_ADDRESS','PATH','LANG'}:raise ValueError('unexpected inherited/remote config override')
    runtime=account['XDG_RUNTIME_DIR']
    import re
    if not re.fullmatch('/run/user/[1-9][0-9]*',runtime):raise ValueError('explicit nonroot account required')
    def same(actual,expected):
        if actual!=expected:raise ValueError('unsafe candidate runtime boundary')
    same(engine['cgroup_manager'],'systemd');same(engine['events_logger'],'none');same(engine['runtime'],'crun')
    same(engine['pull_policy'],'never');same(engine['tmp_dir'],'/srv/shop/tmp/libpod');same(engine['volume_path'],'/srv/shop/volumes')
    same(network,{'network_backend':'netavark','network_config_dir':'/srv/shop/containers/networks','default_rootless_network_cmd':'pasta'})
    same(containers['containers'],{'log_driver':'k8s-file','log_size_max':10485760})
    for path in [*engine['conmon_path'],*engine['helper_binaries_dir'],*engine['runtimes']['crun'],storage['storage']['options']['overlay']['mount_program']]:
        if not re.fullmatch('/nix/store/[a-z0-9]{32}-[^/]+/(?:bin|libexec/podman)(?:/[^/]+)?',path):raise ValueError('unpinned helper path')
    settings=storage['storage'];same(settings['driver'],'overlay')
    same(settings['graphroot'],'/srv/shop/containers/storage');same(settings['rootless_storage_path'],settings['graphroot'])
    same(settings['runroot'],runtime+'/shop-containers')
    same(account['HOME'],'/srv/shop');same(account['TMPDIR'],'/srv/shop/tmp')
    same(account['XDG_CONFIG_HOME'],'/srv/shop/control/runtime');same(account['XDG_DATA_HOME'],'/srv/shop/containers')
    same(account['DBUS_SESSION_BUS_ADDRESS'],'unix:path='+runtime+'/bus')
    same(candidate['unitDir'],'/etc/containers/systemd/users/'+runtime.rsplit('/',1)[1])
    for key in ('CONTAINERS_CONF','CONTAINERS_STORAGE_CONF','CONTAINERS_REGISTRIES_CONF'):
        if not account[key].startswith('/nix/store/'):raise ValueError('runtime config must be immutable')
    for script in (candidate['podmanText'],candidate['generatorText']):
        if '/bin/env -i ' not in script or 'set -eu' not in script:raise ValueError('ambient override boundary missing')
        subprocess.run(['sh','-n'],input=script,text=True,capture_output=True,check=True,timeout=5)
    for token in ('--user --no-kmsg-log', 'QUADLET_UNIT_DIRS='+candidate['unitDir'], 'PODMAN=/nix/store/'):
        if token not in candidate['generatorText']:raise ValueError('isolated generator contract missing')
    if '--expected /srv/shop/control/expected.json' not in candidate['podmanText']:raise ValueError('runtime startup guard missing')
    return True



def validate_generator_discovery(candidate):
    """Validate evaluated instance-only discovery; never start/reload a manager."""
    import configparser
    import re
    runtime = candidate['environment']['XDG_RUNTIME_DIR']
    if not re.fullmatch('/run/user/[1-9][0-9]*', runtime):raise ValueError('explicit new nonroot UID required')
    uid = runtime.rsplit('/',1)[1]
    expected = 'systemd/system/user@'+uid+'.service.d/50-shop-generators.conf'
    if candidate['managerDropinPath'] != expected:raise ValueError('instance-only user manager required')
    bundle = candidate['generatorBundle']
    if not re.fullmatch('/nix/store/[0-9a-df-np-sv-z]{32}-shop-user-generators-'+uid,bundle):raise ValueError('immutable account-only generator bundle required')
    parser=configparser.ConfigParser(interpolation=None,strict=True)
    parser.optionxform=str
    try:parser.read_string(candidate['managerDropinText'])
    except configparser.Error as error:raise ValueError('closed manager drop-in required') from error
    if parser.defaults() or parser.sections()!=['Service'] or dict(parser['Service'])!={'Environment':'SYSTEMD_GENERATOR_PATH='+bundle}:
        raise ValueError('closed single-directory generator discovery required')
    return True


def validate_quadlet_storage(text):
    """Require explicit candidate tmpfs bounds; actual mount proof is separate."""
    import configparser
    config=configparser.ConfigParser(strict=False,interpolation=None)
    config.optionxform=str;config.read_string(text)
    container=config['Container']
    if any(container.get(key)!=value for key,value in {'ReadOnly':'true','ReadOnlyTmpfs':'false','ShmSize':'32m','Tmpfs':'/tmp:rw,size=32m,mode=1777'}.items()):raise ValueError('implicit or unbounded candidate tmpfs')
    if sum(line.startswith('Tmpfs=') for line in text.splitlines())!=1:raise ValueError('unexpected extra writable tmpfs')
    return True


def evaluate():
    start=time.monotonic()
    metadata=json.loads(run(['nix','eval','--json','./ops/nixos#deploymentMetadata.x86_64-linux']))
    if metadata['productionActivation'] is not False or len(metadata['imageDerivations'])!=4:raise ValueError('candidate metadata invalid')
    diagnostics=metadata['postgresDiagnostics'];command=diagnostics['command']
    if (diagnostics['runtimeQualified'] is not False or len(command)<4 or command[1]!='-I'
        or not command[0].startswith('/nix/store/') or not command[0].endswith('/bin/python3')
        or command[2]!=diagnostics['workerSource'] or not command[2].startswith('/nix/store/')
        or not command[2].endswith('/libexec/shop/postgres_entrypoint.py')
        or not command[3].startswith('/nix/store/') or not command[3].endswith('/bin/postgres')):
        raise ValueError('candidate PG console filter image linkage missing')
    expr='let f = builtins.getFlake "git+file://${toString ./.}?dir=ops/nixos"; in import ./ops/nixos/tests/shop.nix { inherit (f.inputs) nixpkgs; shopModule = f.nixosModules.shop; }'
    fixture=json.loads(run(['nix','eval','--json','--impure','--expr',expr]))
    if not all(fixture['disabled'].values()):raise ValueError('default module changes protected scope')
    validate_runtime_contract(fixture['runtimeCandidate'])
    validate_generator_discovery(fixture['runtimeCandidate'])
    for name in ('app','worker','postgres','gateway'):
        validate_quadlet_storage((ROOT/'ops/quadlet'/('shop-'+name+'.container')).read_text())
    candidate=fixture['syntheticCandidate']
    from check_postgresql_config import validate_candidate
    validate_candidate(candidate['databaseConfig'],candidate['databaseHba'])
    if not candidate['bootstrapArtifact'].startswith('/nix/store/') or ' -I -c ' not in candidate['bootstrapScript'] or '--apply|--help' not in candidate['bootstrapScript']:raise ValueError('bootstrap artifact missing isolated explicit-action entrypoint')
    subprocess.run(['sh','-n'],input=candidate['bootstrapScript'],text=True,capture_output=True,check=True,timeout=5)
    failed=[x['message'] for x in candidate['assertions'] if not x['assertion']]
    if failed:raise ValueError('synthetic module assertions failed: '+str(failed))
    bounds=candidate['bounds']
    if any(bounds.get(k)!=v for k,v in {'CPUQuota':'200%','MemoryHigh':'6G','MemoryMax':'8G','TasksMax':1024}.items()):raise ValueError('aggregate resource contract invalid')
    if candidate['managerDropinPaths']!=[fixture['runtimeCandidate']['managerDropinPath']] or candidate['disabledManagerDropinPaths']:raise ValueError('generator discovery escaped new manager instance')
    actual_discovery=dict(fixture['runtimeCandidate'], managerDropinText=candidate['managerDropinText'], generatorBundle=candidate['managerGeneratorBundle'])
    validate_generator_discovery(actual_discovery)
    if not candidate['globalUserGeneratorsUnchanged'] or not candidate['existingManagerConfigUnchanged'] or not candidate['existingAccountUnchanged']:raise ValueError('global or pre-existing owner/manager configuration changed')
    if not candidate['automaticGlobalLingerUnchanged'] or not candidate['shopLingerUnmanagedByGlobalService']:
        raise ValueError('global linger policy changed or new shop enrolled into shared management')
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_deployment.py');stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream).run(suite)
    if result.testsRun<4 or not result.wasSuccessful() or result.skipped:raise ValueError('guard tests failed: '+stream.getvalue())
    probe_suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_process_probe.py')
    probe_result=unittest.TextTestRunner(stream=stream).run(probe_suite)
    if probe_result.testsRun<14 or not probe_result.wasSuccessful() or probe_result.skipped:raise ValueError('process probe controls failed: '+stream.getvalue())
    runtime_suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_rootless_runtime.py')
    runtime_result=unittest.TextTestRunner(stream=stream).run(runtime_suite)
    if runtime_result.testsRun<7 or not runtime_result.wasSuccessful() or runtime_result.skipped:raise ValueError('runtime config controls failed: '+stream.getvalue())
    print(f'DEPLOYMENT_EVAL_PASS checks=16 tests={result.testsRun+probe_result.testsRun+runtime_result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
    print('Candidate evaluation only; unbuilt images, generator/runtime/bootstrap/review/off-host evidence pending')


def validate_profile(profile):
    """Validate an unobserved template, never accept a claimed host observation."""
    expected = {
        'schema_version','selected','evidence_class','host','account','runtime','database','resources',
        'storage','listeners','ingress','objects','integrations','authorization'}
    if not isinstance(profile,dict) or set(profile)!=expected:raise ValueError('closed selected profile required; old cloud/unknown fields forbidden')
    def exact(section, values):
        value=profile[section]
        if not isinstance(value,dict) or set(value)!=set(values):raise ValueError('closed profile section required: '+section)
        if any(type(value[k]) is not type(v) or value[k]!=v for k,v in values.items()):raise ValueError('proposed template cannot assert observed/authorized state: '+section)
    if type(profile['schema_version']) is not int or profile['schema_version']!=1 or profile['selected']!='mx1-rootless' or profile['evidence_class']!='proposed-unobserved':raise ValueError('only current unobserved selected profile supported')
    exact('host',{'name':'mx1','location':None,'machine_id_sha256':None,'configuration_revision':None,'observed':False})
    exact('account',{'name':'shopsvc','uid':None,'gid':None,'subordinate_start':None,'subordinate_count':65536,'outside_claude_dev':True})
    exact('runtime',{'manager':'rootless-podman-quadlet-user-systemd','graphroot':'/srv/shop/containers/storage','image_digests':{'app':None,'worker':None,'postgres':None,'gateway':None},'worker_count':1,'qualified':False})
    exact('database',{'independent_new_cluster':True,'container':'shop-postgres','pgdata':'/srv/shop/postgres','database':None,'role':None,'system_identifier':None,'socket':None,'private_port':None,'backup_identity':None,'existing_cluster_reuse':False})
    exact('resources',{'ancestor':None,'cpu_quota_percent':200,'memory_high_bytes':6442450944,'memory_max_bytes':8589934592,'tasks_max':1024,'concurrency_qualified':False,'all_descendants_qualified':False,'existing_parent_changes':False})
    exact('storage',{'parent_dataset':None,'database_dataset':None,'parent_quota_bytes':85899345920,'database_quota_bytes':53687091200,'snapshot_and_descendant_accounting':True,'writable_categories':['graphroot','images','volumes','postgres-data-index-wal','tmp','logs','certificates','spool','backups'],'observed':False})
    exact('listeners',{'example_http_loopback_port':18080,'example_tls_loopback_port':18443,'allocated':False,'preserve_ports':[80,443,18444],'http3':False})
    ingress=profile['ingress']
    if not isinstance(ingress,dict) or ingress.get('mode') not in (None,'A-passthrough','B-existing-termination'):raise ValueError('mutually exclusive ingress mode required')
    mode=ingress['mode']; copy=dict(profile);copy['ingress']=dict(ingress,mode=None)
    original=profile;profile=copy
    exact('ingress',{'mode':None,'public_activation':False,'unchanged_complete_route_evidence':[],'certificate_owner':None,'http01_tlsalpn01_first':True,'dns01_proves_routing':False,'protected_proxy_change':False,'proxy_protocol_addition':False,'trust_inbound_headers':False,'dns_changes':False})
    exact('objects',{'public_region':'gra','private_region':'gra','recovery_evidence_region':'sbg','project':None,'public_namespace':None,'private_namespace':None,'recovery_namespace':None,'evidence_namespace':None,'distinct_credentials_qualified':False,'retention_acl_billing_qualified':False,'protected_project':'001-xspi-pro'})
    exact('integrations',{'smtp_interface':None,'monitoring_interface':None,'change_existing_services':False,'shop_backup_owner':None})
    exact('authorization',{'inventory_complete':False,'activation_impact_complete':False,'protected_actions':[],'generic_approval':False,'rollback':'shop-only-preserve-committed-records'})
    return original


def profiles():
    started=time.monotonic()
    profile=json.loads((ROOT/'ops/config/deployment-profiles.json').read_text());validate_profile(profile)
    for name in ('docs/host-protection-inventory.md','docs/shop-resource-allowlist.md','docs/nixos-activation-impact.md','ops/qualification/mx1.md'):
        if not (ROOT/name).is_file() or 'NOT OBSERVED' not in (ROOT/name).read_text():raise ValueError('missing explicit unobserved qualification document')
    value=json.loads(run(['nix','eval','--json','--impure','--expr','(import ./ops/nixos/profiles/mx1-template.nix {}).services.xspiShop.enable']))
    if value is not False:raise ValueError('template activates shop')
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_deployment_profiles.py');stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite)
    if result.testsRun<5 or not result.wasSuccessful() or result.skipped:raise ValueError('profile controls failed: '+stream.getvalue())
    print(f'DEPLOYMENT_PROFILES_PASS checks=6 tests={result.testsRun} duration_seconds={time.monotonic()-started:.3f}')
    print('Offline unobserved templates only; no host/provider/routing/activation evidence')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('lane',choices=['deployment-eval','deployment-build','deployment-boot','deployment-profiles']);p.add_argument('--runner-authorization',type=Path);a=p.parse_args()
    if a.lane=='deployment-eval':evaluate();return
    if a.lane=='deployment-boot':
        from check_backend import runner_authorization
        runner_authorization(a.runner_authorization or os.environ.get('SHOP_DEPLOYMENT_RUNNER_AUTHORIZATION'),action='owned-synthetic-rootless-lifecycle')
        raise ValueError('PENDING_RUNTIME_FIXTURES: off-host driver/bootstrap/images not yet qualified; no lifecycle pass')
    if a.lane=='deployment-build':raise ValueError('PENDING_EXACT_RUNTIME_REVIEW: candidate definitions evaluated only; exact image/transitive review and build resource qualification required')
    profiles()

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print('DEPLOYMENT_FAIL: '+str(error),file=sys.stderr);raise SystemExit(1)
