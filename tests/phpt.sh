#!/bin/bash
set -euo pipefail
mkdir -p /build/test-ini
python3 - <<'PY'
import json
from pathlib import Path
manifest = json.loads(Path('/out/manifest.json').read_text())
for package in manifest['packages']:
    for ini in (Path('/build/packages') / package / 'usr/share' / package).glob('*.ini'):
        if ini.name == 'php.ini':
            continue
        priority = ini.read_text().splitlines()[0].split('=')[1]
        (Path('/build/test-ini') / (priority + '-' + ini.name)).write_text(ini.read_text())
PY
export PHP_INI_SCAN_DIR=/build/test-ini
export TEST_PHP_EXECUTABLE=/build/cli/sapi/cli/php
export TEST_PHP_CGI_EXECUTABLE=/build/cli/sapi/cgi/php-cgi
export TEST_PHP_ARGS='-d extension_dir=/build/cli/modules'
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1
cd /build/source
# Upload progress PHPTs require a feature intentionally disabled by the official
# EOL patch. Its absence AND normal uploads are explicitly tested in fpm.py.
find tests/basic ext/session/tests ext/json/tests ext/pdo_sqlite/tests \
  -name '*.phpt' ! -path 'ext/session/tests/rfc1867*' | sort > /out/evidence/phpt-selected.txt
set +e
"$TEST_PHP_EXECUTABLE" -d extension_dir=/build/cli/modules run-tests.php \
  -q -p "$TEST_PHP_EXECUTABLE" -c /dev/null \
  -d extension_dir=/build/cli/modules -r /out/evidence/phpt-selected.txt \
  -w /out/evidence/phpt-failed.txt > /out/evidence/phpt.log 2>&1
result=$?
set -e
tail -35 /out/evidence/phpt.log
find tests/basic ext/session/tests ext/json/tests ext/pdo_sqlite/tests \
  \( -name '*.diff' -o -name '*.out' -o -name '*.exp' \) -print0 \
  | tar --null -T - -czf /out/evidence/phpt-failures.tar.gz
exit "$result"
