#!/usr/bin/env python3
"""Fresh allowlisted static build for the separately qualified public browser path."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from check_frontend import ROOT,copy_inputs,manifest,safe_env,source_policy,scan_output,command


def toolchain(env):
    expected={'node':'v24.22.0','npm':'11.19.1'}
    for name,version in expected.items():
        selected=env.get('SHOP_'+name.upper(),'')
        resolved=shutil.which(name,path=env.get('PATH',''))
        if (not selected.startswith('/nix/store/') or not resolved
                or Path(selected).resolve()!=Path(resolved).resolve()
                or command([selected,'--version'],ROOT,env,15).strip()!=version):
            raise ValueError('exact frozen frontend toolchain required')
    return {'node':'24.22.0','npm':'11.19.1'}


def build_public(destination):
    raw=Path(destination)
    if raw.is_symlink():raise ValueError('fresh owned browser public directory required')
    destination=raw.resolve()
    # Caller owns a fresh private scratch directory. No stale dist or repo node_modules.
    if (not destination.is_dir() or destination.is_symlink() or any(destination.iterdir())
            or not destination.is_relative_to((ROOT/'.scratch').resolve())):
        raise ValueError('fresh owned browser public directory required')
    identity=toolchain(os.environ)
    scratch=destination.parent/'frontend-build';scratch.mkdir(mode=0o700)
    project=scratch/'frontend'
    inputs=json.loads((ROOT/'frontend/build-inputs.json').read_text())
    copy_inputs(ROOT/'frontend',project,manifest(inputs))
    (project/'build-inputs.json').write_text(json.dumps(inputs))
    env=safe_env(scratch)
    command(['npm','ci','--registry=https://registry.npmjs.org','--no-audit','--no-fund'],project,env,150)
    source_policy(project,env)
    for args in (['npm','run','check'],['npm','run','build'],['npm','test']):
        command(args,project,env,150)
    inventory,_=scan_output(project/'dist')
    shutil.copytree(project/'dist',destination,dirs_exist_ok=True)
    print(json.dumps({'status':'PUBLIC_BROWSER_BUILD_PASS','frontend_toolchain':identity,'artifacts':inventory}),flush=True)


if __name__=='__main__':
    try:build_public(sys.argv[1])
    except (ValueError,OSError,subprocess.SubprocessError,IndexError):
        raise SystemExit('PUBLIC_BROWSER_BUILD_FAIL: exact fresh public build unavailable') from None
