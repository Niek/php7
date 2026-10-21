#!/bin/bash
# Run from an extracted, verified release bundle as root.
set -euo pipefail
test "$(id -u)" = 0 || { echo 'Run as root.' >&2; exit 1; }
cd -- "$(dirname -- "$0")"
command -v python3 >/dev/null || { echo 'Install python3 first.' >&2; exit 1; }
python3 - <<'PY'
import hashlib, json, subprocess
from pathlib import Path
m = json.loads(Path('manifest.json').read_text())
osinfo = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
target = osinfo['ID'].strip('"') + osinfo['VERSION_ID'].strip('"')
if target.startswith('debian10.'):
    target = 'debian10'
assert target == m['target'], 'Wrong distribution: expected ' + m['target']
assert subprocess.check_output(['dpkg', '--print-architecture']).decode().strip() == 'amd64'
assert len(list(Path('packages').glob('*.deb'))) == len(m['packages']), 'Unexpected package files'
for p in m['packages'].values():
    assert hashlib.sha256((Path('packages') / p['filename']).read_bytes()).hexdigest() == p['sha256']
print('Target architecture and package checksums verified.')
PY
mapfile -t installed < <(dpkg-query -W -f='${binary:Package} ${db:Status-Status}\n' 'php7.4*' 'libapache2-mod-php7.4' 2>/dev/null | awk '$2 == "installed" {print $1}' || true)
# Refuse removals, downgrades, or broken dependencies before changing anything.
apt-get --simulate --no-remove install ./packages/*.deb
for package in "${installed[@]}"; do
  candidate=$(find packages -maxdepth 1 -name "${package%%:*}_*.deb" -print -quit)
  if [ -z "$candidate" ]; then
    echo "This release does not replace installed package $package. Review its compatibility before proceeding." >&2
    exit 1
  fi
  old=$(dpkg-query -W -f='${Version}' "$package")
  new=$(dpkg-deb -f "$candidate" Version)
  dpkg --compare-versions "$new" ge "$old" || { echo "Refusing downgrade of $package" >&2; exit 1; }
done
if [ "${#installed[@]}" -gt 0 ] && ! command -v dpkg-repack >/dev/null; then
  echo 'Install the native dpkg-repack package first so original PHP packages can be saved.' >&2
  exit 1
fi
backup=/var/backups/php7-$(date -u +%Y%m%dT%H%M%SZ)
install -d -m 0700 "$backup/packages"
dpkg-query -W > "$backup/installed-packages.tsv"
paths=()
for path in etc/php/7.4 etc/systemd/system/php7.4-fpm.service.d usr/lib/php/20190902; do
  [ ! -e "/$path" ] || paths+=("$path")
done
if [ "${#paths[@]}" -gt 0 ]; then
  tar -C / -czf "$backup/config-and-extensions.tar.gz" "${paths[@]}"
else
  tar -C / -czf "$backup/config-and-extensions.tar.gz" --files-from=/dev/null
fi
if [ "${#installed[@]}" -gt 0 ]; then
  (cd "$backup/packages"; dpkg-repack "${installed[@]}")
fi
was_active=0
if command -v systemctl >/dev/null && systemctl is-active --quiet php7.4-fpm; then was_active=1; fi
apt-get --no-remove -y -o Dpkg::Options::=--force-confold install ./packages/*.deb
php7.4 --version
php-fpm7.4 --test
if [ "$was_active" = 1 ]; then
  systemctl restart php7.4-fpm
  systemctl is-active --quiet php7.4-fpm
fi
echo "Packages installed; rollback files: $backup"
echo 'Validate your application and restart long-running PHP workers. See README.md before removing any workaround.'
