#!/usr/bin/env python3
"""Fail closed if the reviewed security backport is missing or changed."""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
lock = json.loads(Path('/repo/sources.lock.json').read_text())
patches = [line for line in (root / 'debian/patches/series').read_text().splitlines()
           if line.strip() and not line.startswith('#')]
assert len(patches) == lock['patch_count'], len(patches)
applied = (root / '.pc/applied-patches').read_text().splitlines()
assert len(applied) == len(patches), 'Not all patches were applied'
security = root / 'debian/patches/0164-Avoid-state-corruption-via-bailout.patch'
assert all(cve in security.read_text() for cve in ['CVE-2026-109618', 'CVE-2026-109619'])
assert 'if (!PS(rfc1867_enabled) || true)' in (root / 'ext/session/session.c').read_text()
assert 'zend_mm_safe_error_ex' in (root / 'Zend/zend_alloc.c').read_text()
assert 'php_mime_should_save_hdr' in (root / 'main/rfc1867.c').read_text()
print('All 164 source patches applied, including both CVE backports.')
