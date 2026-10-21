#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / 'sources.lock.json').read_text())
assert os.environ['RELEASE_TAG'] == lock['release'], 'Tag must match the reviewed source lock'
targets = json.loads((root / 'targets.json').read_text())
destination = root / 'release'
destination.mkdir()
for target in targets:
    artifact = root / 'artifacts' / ('php7-' + target + '-amd64')
    manifest = json.loads((artifact / 'manifest.json').read_text())
    assert manifest['source_revision'] == os.environ['GITHUB_SHA']
    assert manifest['target'] == target and manifest['architecture'] == 'amd64'
    assert manifest['source'] == lock
    assert (artifact / 'evidence/result.txt').read_text().startswith('PASS:')
    for package in manifest['packages'].values():
        path = artifact / 'packages' / package['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == package['sha256']
        shutil.copyfile(str(path), str(destination / path.name))
    shutil.copyfile(str(artifact / 'manifest.json'), str(destination / ('manifest-' + target + '.json')))
    bundles = list(artifact.glob('php7.4-*.tar.xz'))
    assert len(bundles) == 1
    bundle = bundles[0]
    expected = bundle.with_suffix(bundle.suffix + '.sha256').read_text().split()[0]
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == expected
    shutil.copyfile(str(bundle), str(destination / bundle.name))
subprocess.check_call(['python3', str(root / 'scripts/fetch.py')])
with tarfile.open(str(destination / ('php7.4-sources-' + lock['release'] + '.tar.xz')), 'w:xz') as archive:
    for name in lock['files']:
        archive.add(str(root / '.cache/sources' / name), arcname=name)
    for name in ('sources.lock.json', 'packaging/provenance'):
        archive.add(str(root / name), arcname=name)
shutil.copyfile(str(root / 'sources.lock.json'), str(destination / 'sources.lock.json'))
checksums = [hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name
             for p in sorted(destination.iterdir()) if p.is_file()]
(destination / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
