"""Serve only byte-pinned private static files; never fetch a public shop origin."""
import base64
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path,PurePosixPath
import re
import stat

MANIFEST='shop-release.json'
ENTRY='private-storefront/index.html'
SOURCE_SHA256='ba801dff4adbfdcfa0f1e43cfe1f2d6963780476867da1b5e6f737230a472b5e'
MIMES={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8',
    '.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.woff2':'font/woff2',
    '.png':'image/png','.ico':'image/x-icon'}
LIMIT=8*1024*1024


def require(value):
    if not value:raise ValueError('private_release_unavailable')


def safe_path(value):
    require(type(value) is str)
    path=PurePosixPath(value)
    require(value and path.as_posix()==value and not path.is_absolute() and '\\' not in value
        and not any(part in ('.','..') or part.startswith('.') for part in path.parts))
    return path


class InlineScripts(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=False);self.inside=None;self.parts=[];self.hashes={'script':[],'style':[]}
    def handle_starttag(self,tag,attrs):
        if tag=='style' or tag=='script' and not dict(attrs).get('src'):self.inside=tag;self.parts=[]
    def handle_data(self,data):
        if self.inside:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag==self.inside:
            raw=''.join(self.parts).encode();self.hashes[tag].append('sha256-'+base64.b64encode(hashlib.sha256(raw).digest()).decode())
            self.inside=None


def script_policy(raw):
    parser=InlineScripts();parser.feed(raw.decode('utf-8'));require(not parser.inside)
    hashes=lambda tag:' '.join("'"+value+"'" for value in sorted(set(parser.hashes[tag])))
    return "default-src 'none'; script-src 'self' "+hashes('script')+"; style-src 'self' "+hashes('style')+"; img-src 'self'; font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"


def read_fd(root_fd,relative,limit=LIMIT):
    path=safe_path(relative);current=os.dup(root_fd)
    try:
        for name in path.parts[:-1]:
            child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=current)
            os.close(current);current=child
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=current)
        try:
            before=os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and 0<before.st_size<=limit)
            chunks=[];remaining=before.st_size+1
            while remaining:
                chunk=os.read(fd,min(remaining,65536))
                if not chunk:break
                chunks.append(chunk);remaining-=len(chunk)
            raw=b''.join(chunks);after=os.fstat(fd)
            fields=lambda st:(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
            require(fields(before)==fields(after) and len(raw)==before.st_size)
            return raw
        finally:os.close(fd)
    finally:os.close(current)


def make_manifest(root):
    root=Path(root)
    require(root.is_dir() and not root.is_symlink())
    entries=sorted(root.rglob('*'));require(len(entries)<=512)
    files={}
    root_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        for path in entries:
            require(not path.is_symlink())
            if not path.is_file() or path.name==MANIFEST:continue
            relative=path.relative_to(root).as_posix();safe_path(relative)
            require(path.suffix in MIMES and not path.name.endswith('.map'))
            raw=read_fd(root_fd,relative)
            if relative in ('index.html','support/index.html'):
                require(not re.search(rb'Supporting Hours Bundle|sll-xspi-mc|Configure your licence|\[PRICE\]',raw,re.I))
            files[relative]={'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw),'content_type':MIMES[path.suffix]}
        require(ENTRY in files and 'index.html' in files)
        return {'schema':1,'source_sha256':SOURCE_SHA256,'entry':ENTRY,'files':files,
            'public_files':['index.html','support/index.html'],'runtime_qualified':False}
    finally:os.close(root_fd)


def encode_manifest(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


def read_asset(root,expected,relative):
    require(type(expected) is str and re.fullmatch('[a-f0-9]{64}',expected))
    path=safe_path(relative)
    require(relative==ENTRY or relative.startswith('_astro/'))
    root=Path(root);require(root.is_absolute() and root.resolve()==root)
    root_fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        encoded=read_fd(root_fd,MANIFEST,131072)
        require(hashlib.sha256(encoded).hexdigest()==expected)
        manifest=json.loads(encoded)
        require(type(manifest) is dict and set(manifest)=={'schema','source_sha256','entry','files','public_files','runtime_qualified'}
            and type(manifest['schema']) is int and manifest['schema']==1
            and manifest['source_sha256']==SOURCE_SHA256 and manifest['entry']==ENTRY
            and manifest['runtime_qualified'] is False)
        row=manifest['files'].get(relative)
        require(type(row) is dict and set(row)=={'sha256','size','content_type'}
            and path.suffix in MIMES and row['content_type']==MIMES[path.suffix])
        raw=read_fd(root_fd,relative)
        require(type(row['size']) is int and len(raw)==row['size'] and hashlib.sha256(raw).hexdigest()==row['sha256'])
        return raw,row['content_type'],script_policy(raw) if path.suffix=='.html' else None
    finally:os.close(root_fd)
