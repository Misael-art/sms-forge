#!/usr/bin/env python3
"""Discover official releases; install hash-bound candidates in parallel, never auto-promote."""
import argparse
import contextlib
import fcntl
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
import time
import urllib.parse
import urllib.request
from blastem_sms import ARCHIVE_SHA, BINARY_SHA, RUNTIME, URL, runtime, sha, write_json

PAGE='https://www.retrodev.com/blastem/downloads.html'
CANDIDATES=RUNTIME.parent/'candidates'

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            self.links += [v for k,v in attrs if k=='href']

def official_url(url):
    u=urllib.parse.urlparse(url)
    if u.scheme!='https' or u.netloc!='www.retrodev.com' or not u.path.startswith('/blastem/') or u.query or u.fragment:
        raise ValueError('only explicit official HTTPS BlastEm downloads accepted')
    return url

def fetch(url):
    official_url(url)
    with urllib.request.urlopen(url,timeout=30) as r:
        official_url(r.geturl())
        data=r.read(64*1024*1024+1)
    if len(data)>64*1024*1024: raise ValueError('download exceeds bounded size')
    return data

def releases():
    data=fetch(PAGE); parser=Links();parser.feed(data.decode('utf8'))
    rows=[]
    for link in parser.links:
        url=urllib.parse.urljoin(PAGE,link)
        match=re.search(r'/blastem64-(\d+\.\d+\.\d+)\.tar\.gz$',url)
        if match:
            official_url(url);rows.append({'version':match[1],'url':url,'platform':'linux_x86_64'})
    if not rows: raise ValueError('official release page changed; no stable Linux x86_64 archives discovered')
    return {'schema':'blastem_release_discovery_v1','checked_at':time.time(),'source':PAGE,
            'page_sha256':hashlib.sha256(data).hexdigest(),'releases':rows,
            'active_qualified':{'version':'1.0.0','url':URL,'archive_sha256':ARCHIVE_SHA,'binary_sha256':BINARY_SHA},
            'policy':'discovery_does_not_change_pin_or_qualify_candidates'}

def validate_manifest(doc):
    if not isinstance(doc,dict) or set(doc)!={'version','url','archive_sha256','binary_sha256'}:
        raise ValueError('manifest requires version/url/archive_sha256/binary_sha256')
    if not isinstance(doc['version'],str) or not re.fullmatch(r'\d+\.\d+\.\d+',doc['version']):
        raise ValueError('invalid release version')
    official_url(doc['url'])
    if doc['url']!=f'https://www.retrodev.com/blastem/blastem64-{doc["version"]}.tar.gz':
        raise ValueError('release version and archive URL differ')
    for key in ('archive_sha256','binary_sha256'):
        if not isinstance(doc[key],str) or not re.fullmatch('[0-9a-f]{64}',doc[key]):
            raise ValueError('explicit SHA256 required; do not learn expected hashes from a failed install')
    return doc

def verify(path):
    path=Path(path).resolve();doc=json.loads((path/'candidate.json').read_text()); expected=validate_manifest(doc['expected'])
    if sha(path/'release.tar.gz')!=expected['archive_sha256']: raise ValueError('candidate archive hash diverges')
    if sha(path/'runtime/blastem')!=expected['binary_sha256']: raise ValueError('candidate executable hash diverges')
    for p in (path/'runtime').rglob('*'):
        if path/'runtime' not in p.resolve().parents:raise ValueError('candidate path escapes runtime')
    actual={str(p.relative_to(path/'runtime')):sha(p) for p in (path/'runtime').rglob('*') if p.is_file()}
    if actual!=doc.get('files'): raise ValueError('candidate files diverge')
    links={str(p.relative_to(path/'runtime')):os.readlink(p) for p in (path/'runtime').rglob('*') if p.is_symlink()}
    if links!=doc.get('links',{}):raise ValueError('candidate symlinks diverge')
    if doc.get('qualified') is not False: raise ValueError('candidate cannot self-promote')
    return {'ok':True,'path':str(path),'version':expected['version'],'qualified':False,'expected':expected}

def install_candidate(manifest):
    expected=validate_manifest(manifest);CANDIDATES.mkdir(parents=True,exist_ok=True)
    name=expected['version']+'-'+expected['archive_sha256'][:16]
    dest=CANDIDATES/name
    with open(CANDIDATES/'install.lock','w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if dest.exists():
            old=json.loads((dest/'candidate.json').read_text())
            if old.get('expected')!=expected: raise ValueError('parallel installation manifest differs')
            return verify(dest)
        with tempfile.TemporaryDirectory(dir=CANDIDATES,prefix='candidate-') as t:
            tmp=Path(t);archive=tmp/'release.tar.gz';archive.write_bytes(fetch(expected['url']))
            if sha(archive)!=expected['archive_sha256']: raise ValueError('release archive differs from expected SHA256')
            with tarfile.open(archive) as tar:
                members=tar.getmembers()
                if len(members)>10000 or sum(m.size for m in members)>256*1024*1024:
                    raise ValueError('archive expands beyond install bounds')
                if any(m.islnk() or not (m.isfile() or m.isdir() or m.issym()) for m in members):
                    raise ValueError('archive hardlinks or special files rejected')
                tar.extractall(tmp/'unpack',filter='data')
            root=tmp/'unpack'/('blastem64-'+expected['version'])
            if sha(root/'blastem')!=expected['binary_sha256']: raise ValueError('release binary differs from expected SHA256')
            shutil.move(root,tmp/'runtime');shutil.rmtree(tmp/'unpack')
            write_json(tmp/'candidate.json',{'schema':'blastem_parallel_candidate_v1','expected':expected,'qualified':False,
                       'installed_at':time.time(),'files':{str(p.relative_to(tmp/'runtime')):sha(p) for p in (tmp/'runtime').rglob('*') if p.is_file()},
                       'links':{str(p.relative_to(tmp/'runtime')):os.readlink(p) for p in (tmp/'runtime').rglob('*') if p.is_symlink()},
                       'hash_trust':'explicit_manifest_from_curator_not_an_upstream_signature'})
            os.rename(tmp,dest)
    return verify(dest)

def self_check():
    from unittest.mock import patch
    good={'version':'1.0.0','url':URL,'archive_sha256':ARCHIVE_SHA,'binary_sha256':BINARY_SHA}
    validate_manifest(good)
    for bad in ({**good,'url':'https://example.org/a'},{**good,'version':'../x'},{**good,'binary_sha256':'auto'}):
        try: validate_manifest(bad)
        except ValueError: pass
        else: raise AssertionError('bad maintenance manifest accepted')
    with tempfile.TemporaryDirectory() as t:
        root=Path(t);(root/'runtime').mkdir();(root/'release.tar.gz').write_bytes(b'archive');(root/'runtime/blastem').write_bytes(b'binary')
        expected={**good,'archive_sha256':sha(root/'release.tar.gz'),'binary_sha256':sha(root/'runtime/blastem')}
        write_json(root/'candidate.json',{'expected':expected,'qualified':False,'files':{'blastem':expected['binary_sha256']}})
        assert verify(root)['ok']
        (root/'runtime/blastem').write_bytes(b'tampered')
        try: verify(root)
        except ValueError: pass
        else: raise AssertionError('hash divergence accepted')
    print('[SELF-CHECK OK] Release manifest restrictions and candidate hash tamper rejection')
    return 0

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--self-check',action='store_true');ap.add_argument('--json')
    sub=ap.add_subparsers(dest='op');sub.add_parser('releases');sub.add_parser('status')
    p=sub.add_parser('install-candidate');p.add_argument('--manifest',required=True)
    p=sub.add_parser('verify');p.add_argument('--installation',required=True)
    a=ap.parse_args()
    try:
        if a.self_check:return self_check()
        if a.op=='releases':result=releases()
        elif a.op=='status':result={'qualified_binary':str(runtime()),'candidates':[verify(p) for p in CANDIDATES.glob('*') if p.is_dir() and (p/'candidate.json').exists()]}
        elif a.op=='install-candidate':result=install_candidate(json.loads(Path(a.manifest).read_text()))
        elif a.op=='verify':result=verify(a.installation)
        else:ap.error('choose releases/status/install-candidate/verify')
        if a.json:write_json(a.json,result)
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,KeyError) as e:
        print('[FAIL] '+str(e));return 1

if __name__=='__main__':raise SystemExit(main())
