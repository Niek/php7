#!/bin/bash
set -euo pipefail
source /repo/scripts/apt.sh
apt-get install -y --no-install-recommends python3 ca-certificates
# Installing through APT proves dependency closure in a clean target, without
# the compiler or development libraries from the build container.
apt-get install -y --no-install-recommends /out/packages/*.deb
dpkg --audit
php7.4 --version
php7.4 --ini | tee /out/evidence/php-ini.txt
php7.4 -m | tee /out/evidence/modules.txt
php-fpm7.4 --test
python3 - <<'PY'
from pathlib import Path
import subprocess
files = [Path('/usr/bin/php7.4'), Path('/usr/sbin/php-fpm7.4')]
files += list(Path('/usr/lib/php/20190902').glob('*.so'))
with open('/out/evidence/ldd.txt', 'w') as log:
    for path in files:
        output = subprocess.check_output(['ldd', str(path)], universal_newlines=True)
        log.write(str(path) + '\n' + output)
        assert 'not found' not in output, output
assert not Path('/usr/bin/gcc').exists(), 'Runtime test contaminated by build dependencies'
PY
php7.4 /repo/tests/smoke.php | tee /out/evidence/extensions.txt
python3 /repo/tests/fpm.py | tee /out/evidence/fpm-tests.json
# Verify configuration and administrator module state survive reinstallation.
echo '; administrator php.ini setting' >> /etc/php/7.4/fpm/php.ini
echo '; administrator pool setting' >> /etc/php/7.4/fpm/pool.d/www.conf
echo 'date.timezone = Europe/Rome' > /etc/php/7.4/cli/conf.d/99-custom.ini
mkdir -p /etc/systemd/system/php7.4-fpm.service.d
echo '# administrator service override' > /etc/systemd/system/php7.4-fpm.service.d/local.conf
phpdismod -v 7.4 -s ALL bz2
sha256sum /etc/php/7.4/fpm/php.ini /etc/php/7.4/fpm/pool.d/www.conf \
  /etc/php/7.4/cli/conf.d/99-custom.ini /etc/systemd/system/php7.4-fpm.service.d/local.conf > /tmp/config-sha256
apt-get install --reinstall -y -o Dpkg::Options::=--force-confold /out/packages/*.deb
sha256sum -c /tmp/config-sha256 | tee /out/evidence/config-preservation.txt
test ! -e /etc/php/7.4/fpm/conf.d/20-bz2.ini
test ! -e /etc/php/7.4/cli/conf.d/20-bz2.ini
phpenmod -v 7.4 -s ALL bz2
php7.4 /repo/tests/smoke.php >> /out/evidence/extensions.txt
php-fpm7.4 --test
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /out/evidence/runtime-packages.tsv
printf 'PASS: clean install, dependencies, modules, FPM, uploads, OOM recovery, configuration preservation\n' > /out/evidence/result.txt
