#!/usr/bin/env python3
"""Prepare a private Astro snapshot manifest; no upload, publication or activation."""
import argparse
import hashlib
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from shop.shb.private_release import make_manifest,encode_manifest,MANIFEST


def compile_release(root):
    root=Path(root).resolve()
    value=make_manifest(root);encoded=encode_manifest(value)
    (root/MANIFEST).write_bytes(encoded)
    digest=hashlib.sha256(encoded).hexdigest()
    print(f'SHB_PRIVATE_RELEASE_PASS checks=1 files={len(value["files"])} sha256={digest} runtime_qualified=false')
    return digest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dist',type=Path,default=ROOT/'frontend/dist')
    compile_release(parser.parse_args().dist)
