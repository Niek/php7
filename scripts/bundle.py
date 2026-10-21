#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path
import sys
import tarfile

root = Path(__file__).resolve().parents[1]
target = sys.argv[1]
assert target in json.loads((root / 'targets.json').read_text())
output = root / 'out' / target
assert (output / 'evidence/result.txt').read_text().startswith('PASS:'), 'Runtime tests must pass'
lock = json.loads((root / 'sources.lock.json').read_text())
name = 'php7.4-' + target + '-amd64-' + lock['release']

def normalized(info):
    info.uid = info.gid = 0
    info.uname = info.gname = 'root'
    info.mtime = lock['source_date_epoch']
    return info

with tarfile.open(str(output / (name + '.tar.xz')), 'w:xz') as archive:
    for member in ('packages', 'evidence', 'manifest.json'):
        archive.add(str(output / member), arcname=name + '/' + member, filter=normalized)
    for member in ('README.md', 'SECURITY.md', 'sources.lock.json', 'scripts/install.sh'):
        archive.add(str(root / member), arcname=name + '/' + Path(member).name, filter=normalized)
path = output / (name + '.tar.xz')
(output / (name + '.tar.xz.sha256')).write_text(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n')
print('Verified release bundle: ' + str(path))
