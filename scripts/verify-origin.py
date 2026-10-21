#!/usr/bin/env python3
"""Verify the committed Sury signature -> Sources.gz -> source archive chain."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
proof = root / 'packaging/provenance'
lock = json.loads((root / 'sources.lock.json').read_text())
fingerprint = '15058500A0235D97F5D10063B188E2B695BD4743'
with tempfile.TemporaryDirectory() as home:
    output = subprocess.check_output(['gpgv', '--homedir', home, '--status-fd', '1',
                                      '--keyring', str(proof / 'sury.gpg'),
                                      str(proof / 'InRelease')], universal_newlines=True)
    assert '[GNUPG:] VALIDSIG ' + fingerprint + ' ' in output, 'Unexpected signing key'
release = (proof / 'InRelease').read_text()
section = release.split('\nSHA256:\n', 1)[1].split('\nSHA512:', 1)[0]
digest = hashlib.sha256((proof / 'Sources.gz').read_bytes()).hexdigest()
assert any(line.split() == [digest, str((proof / 'Sources.gz').stat().st_size), 'main/source/Sources.gz']
           for line in section.splitlines()), 'Sources.gz does not match signed Release'
entries = gzip.decompress((proof / 'Sources.gz').read_bytes()).decode().split('\n\n')
entry = next(e for e in entries if '\nVersion: ' + lock['source_version'] + '\n' in '\n' + e + '\n'
             and ('\nPackage: php7.4\n' in '\n' + e + '\n' or '\nPackage: php7.4\r\n' in e))
checksums = entry.split('\nChecksums-Sha256:', 1)[1]
for name, expected in lock['files'].items():
    assert any(len(line.split()) == 3 and line.split()[0] == expected and line.split()[2] == name
               for line in checksums.splitlines()), name + ' not authenticated'
print('PASS: Sury signing key, signed source index and every locked source hash')
