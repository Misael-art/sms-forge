#!/usr/bin/env python3
"""Pack/verify/restore the explicit SMS engine recovery scope, including ignored inputs."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

from host_bootstrap import HostError, checked_members, digest, extract, write_json

ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN = {'.git', '.venv', '.runtime', '__pycache__', '.pytest_cache',
             '.env', 'token', 'id_rsa', 'id_ed25519', 'credentials.json'}


def selected_files(root):
    roots = [root / rel for rel in [
        'AGENTS.md', 'README.md', '.gitignore', 'sdk/README.md',
        'tools/sms_wrapper', 'SMS_projects/luta_mugem_rev2',
        'doc/06_AI_MEMORY_BANK.md', 'doc/agent_learning', 'doc/05_technical',
        'doc/curation/evidence/2026-10-24_mugenesis',
    ]]
    roots += list((root / 'doc/curation').glob('2026-10-2[34]*'))
    roots += list((root / 'doc/continuity').glob('20261024-*'))
    files, excluded = {}, []
    for owner in roots:
        if not owner.exists():
            raise HostError(f'recovery source missing: {owner}')
        candidates = [owner] if owner.is_file() else owner.rglob('*')
        for path in candidates:
            rel = path.relative_to(root)
            if any(part in FORBIDDEN for part in rel.parts) or path.suffix == '.pyc':
                continue
            if path.is_symlink():
                excluded.append({'path': str(rel), 'reason': 'symlink_not_followed'})
                continue
            if path.is_file():
                # The external asset index cannot include itself in its own hash.
                if path.name.startswith('20261024-release-assets'):
                    continue
                files[str(rel)] = path
    return dict(sorted(files.items())), excluded


def pack(root, archive, manifest, runtime_only=False):
    if archive.exists() or manifest.exists():
        raise HostError('archive/manifest already exist; choose a new output')
    files, excluded = selected_files(root)
    if runtime_only:
        prefixes = ('SMS_projects/luta_mugem_rev2/out/', 'SMS_projects/luta_mugem_rev2/data/')
        files = {name: path for name, path in files.items() if name.startswith(prefixes)}
        if not files:
            raise HostError('no rev2 runtime/data files selected')
    archive.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    try:
        with tarfile.open(archive, 'x:gz') as tar:
            for rel, path in files.items():
                before = digest(path)
                info = tar.gettarinfo(path, arcname=rel)
                info.uid = info.gid = 0
                info.uname = info.gname = ''
                info.mode = 0o755 if info.mode & 0o111 else 0o644
                with path.open('rb') as stream:
                    tar.addfile(info, stream)
                if digest(path) != before:
                    raise HostError(f'source changed during packing: {rel}')
                entries.append({'path': rel, 'bytes': info.size, 'sha256': before})
        record = {'schema': 'smsforge.recovery_bundle/v1', 'archive_name': archive.name,
                  'archive_sha256': digest(archive), 'archive_bytes': archive.stat().st_size,
                  'entries': entries, 'excluded': excluded,
                  'scope': ('rev2 data and ignored runtime artifacts' if runtime_only else
                            'rev2 sources/data/generated/history + canonical wrapper + current diagnosis'),
                  'not_included': ['credentials and agent personal settings', 'other projects generated outputs',
                                   'luta_mugen unreadable working-tree changes', 'system packages and caches'],
                  'claim_ceiling': 'recoverability_only_no_runtime_promotion'}
        write_json(manifest, record)
        verify(archive, record)
        return record
    except Exception:
        # Keep partial archive for diagnosis; never announce it as recoverable.
        raise


def verify(archive, record):
    if digest(archive) != record['archive_sha256']:
        raise HostError('archive SHA-256 mismatch')
    entries = record['entries']
    expected = {entry['path']: entry for entry in entries}
    if len(expected) != len(entries):
        raise HostError('duplicate paths in manifest')
    with tarfile.open(archive) as tar:
        members = checked_members(tar, max_bytes=4 * 1024**3)
        actual = {member.name for member in members if member.isfile()}
        if actual != set(expected):
            raise HostError('archive/manifest membership differs')
        for member in members:
            if not member.isfile():
                continue
            ref = expected[member.name]
            h = hashlib.sha256()
            with tar.extractfile(member) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(chunk)
            if member.size != ref['bytes'] or h.hexdigest() != ref['sha256']:
                raise HostError(f'file digest/size mismatch: {member.name}')
    return len(expected)


def restore(archive, record, into):
    verify(archive, record)
    into = into.resolve()
    # Preflight every conflict and symlink parent BEFORE any publication.
    for entry in record['entries']:
        target = into / entry['path']
        for ancestor in [target, *target.parents]:
            if ancestor == into.parent:
                break
            if ancestor.is_symlink():
                raise HostError(f'restore refuses symlink: {ancestor}')
        if target.exists() and (not target.is_file() or digest(target) != entry['sha256']):
            raise HostError(f'restore conflict; existing bytes preserved: {target}')
    into.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.smsforge-restore-', dir=into.parent) as temp:
        staging = Path(temp)
        extract(archive, staging)
        created = []
        try:
            for entry in record['entries']:
                target = into / entry['path']
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    partial = None
                    try:
                        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.restore-', delete=False) as dst:
                            partial = Path(dst.name)
                            with (staging / entry['path']).open('rb') as src:
                                shutil.copyfileobj(src, dst)
                        if digest(partial) != entry['sha256']:
                            raise HostError('staged restore file differs')
                        partial.chmod((staging / entry['path']).stat().st_mode & 0o777)
                        os.link(partial, target)  # Atomic per file, refuses existing targets.
                        created.append((target, entry['sha256']))
                    finally:
                        if partial:
                            partial.unlink(missing_ok=True)
        except Exception:
            for target, sha in reversed(created):
                if target.is_file() and not target.is_symlink() and digest(target) == sha:
                    target.unlink()
            raise
    return len(record['entries'])


def self_check():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        archive = root / 'a.tar.gz'
        data = b'recover'
        with tarfile.open(archive, 'w:gz') as tar:
            info = tarfile.TarInfo('out/a.txt')
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        record = {'archive_sha256': digest(archive), 'entries': [
            {'path': 'out/a.txt', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}
        assert verify(archive, record) == 1
        dest = root / 'dest'
        assert restore(archive, record, dest) == 1
        assert restore(archive, record, dest) == 1
        (dest / 'out/a.txt').write_bytes(b'customized')
        try:
            restore(archive, record, dest)
        except HostError:
            pass
        else:
            raise AssertionError('conflict overwritten')
        assert (dest / 'out/a.txt').read_bytes() == b'customized'
        failing = root / 'interrupted'
        real_copy = shutil.copyfileobj
        calls = 0
        def interrupt_second_copy(src, dst, *args):
            nonlocal calls
            calls += 1
            if calls == 2:  # after complete extraction, during publication staging
                dst.write(b'x')
                raise OSError('injected publication copy failure')
            return real_copy(src, dst, *args)
        with patch.object(shutil, 'copyfileobj', interrupt_second_copy):
            try:
                restore(archive, record, failing)
            except OSError:
                pass
            else:
                raise AssertionError('injected failure was not exercised')
        assert calls == 2 and not (failing / 'out/a.txt').exists()
        assert not list(failing.rglob('.restore-*'))
        assert restore(archive, record, failing) == 1
        bad = dict(record, archive_sha256='0' * 64)
        try:
            verify(archive, bad)
        except HostError:
            pass
        else:
            raise AssertionError('wrong archive digest accepted')
    print('[SELF-CHECK OK] recovery bundle: hashes, exact membership, idempotence, conflict preservation')
    return 0


def main(argv=None):
    if argv == ['--self-check'] or (argv is None and sys.argv[1:] == ['--self-check']):
        return self_check()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['pack', 'verify', 'restore'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--into', type=Path)
    parser.add_argument('--runtime-only', action='store_true', help='pack only rev2 data/out for bootstrap')
    args = parser.parse_args(argv)
    try:
        if args.operation == 'pack':
            record = pack(args.root.resolve(), args.archive, args.manifest, args.runtime_only)
            print(json.dumps({'files': len(record['entries']), 'bytes': record['archive_bytes'],
                              'sha256': record['archive_sha256']}))
        else:
            record = json.loads(args.manifest.read_text())
            if args.operation == 'restore' and not args.into:
                raise HostError('--into required')
            count = verify(args.archive, record) if args.operation == 'verify' else restore(args.archive, record, args.into)
            print('[OK]', args.operation, count, 'files; no game-quality claim')
        return 0
    except (HostError, OSError, ValueError, tarfile.TarError) as error:
        print('[FAIL]', error, file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
