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
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]


def run(args,timeout=60):
    return subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout,check=True).stdout


def evaluate():
    start=time.monotonic()
    metadata=json.loads(run(['nix','eval','--json','./ops/nixos#deploymentMetadata.x86_64-linux']))
    if metadata['productionActivation'] is not False or len(metadata['imageDerivations'])!=4:raise ValueError('candidate metadata invalid')
    expr='let f = builtins.getFlake (toString ./ops/nixos); in import ./ops/nixos/tests/shop.nix { inherit (f.inputs) nixpkgs; shopModule = f.nixosModules.shop; }'
    fixture=json.loads(run(['nix','eval','--json','--impure','--expr',expr]))
    if not all(fixture['disabled'].values()):raise ValueError('default module changes protected scope')
    candidate=fixture['syntheticCandidate']
    failed=[x['message'] for x in candidate['assertions'] if not x['assertion']]
    if failed:raise ValueError('synthetic module assertions failed: '+str(failed))
    bounds=candidate['bounds']
    if any(bounds.get(k)!=v for k,v in {'CPUQuota':'200%','MemoryHigh':'6G','MemoryMax':'8G','TasksMax':1024}.items()):raise ValueError('aggregate resource contract invalid')
    if not candidate['automaticGlobalLingerUnchanged'] or not candidate['shopLingerUnmanagedByGlobalService']:
        raise ValueError('global linger policy changed or new shop enrolled into shared management')
    suite=unittest.TestLoader().discover(str(ROOT/'tests'),pattern='test_deployment.py');stream=io.StringIO()
    result=unittest.TextTestRunner(stream=stream).run(suite)
    if result.testsRun<4 or not result.wasSuccessful() or result.skipped:raise ValueError('guard tests failed: '+stream.getvalue())
    print(f'DEPLOYMENT_EVAL_PASS checks=9 tests={result.testsRun} duration_seconds={time.monotonic()-start:.3f}')
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
