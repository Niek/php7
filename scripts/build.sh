#!/bin/bash
set -euo pipefail
source /repo/scripts/apt.sh
apt-get install -y --no-install-recommends build-essential autoconf bison re2c \
  pkg-config dpkg-dev patch xz-utils python3 ca-certificates \
  libxml2-dev libssl-dev libcurl4-openssl-dev libbz2-dev libedit-dev \
  libpng-dev libjpeg-dev libfreetype6-dev libwebp-dev libicu-dev libonig-dev \
  libzip-dev libsodium-dev libsqlite3-dev libxslt1-dev libsystemd-dev \
  libacl1-dev libapparmor-dev libgmp-dev libpq-dev libffi-dev
mkdir -p /build /out/packages /out/evidence
cd /build
python3 - <<'PY'
import hashlib, json
from pathlib import Path
lock = json.loads(Path('/repo/sources.lock.json').read_text())
for name, expected in lock['files'].items():
    assert hashlib.sha256((Path('/repo/.cache/sources') / name).read_bytes()).hexdigest() == expected, name
PY
# The .dsc is unsigned. Trust comes from the reviewed SHA256 lock and retained
# signed repository metadata, not from an implicit dpkg-source signature check.
dpkg-source --no-check -x /repo/.cache/sources/*.dsc /build/source
python3 /repo/scripts/check-source.py /build/source
export SOURCE_DATE_EPOCH
SOURCE_DATE_EPOCH=$(python3 -c 'import json; print(json.load(open("/repo/sources.lock.json"))["source_date_epoch"])')
export CFLAGS='-O2 -g -fstack-protector-strong -fPIC -Wformat -Werror=format-security'
export CXXFLAGS="$CFLAGS"
export CPPFLAGS='-D_FORTIFY_SOURCE=2'
export LDFLAGS='-Wl,-z,relro,-z,now -Wl,--as-needed'
common=(--prefix=/usr --libdir=/usr/lib/php --libexecdir=/usr/lib/php
  --datadir=/usr/share/php/7.4 --program-suffix=7.4 --sysconfdir=/etc
  --localstatedir=/var --mandir=/usr/share/man --disable-all --disable-debug
  --disable-rpath --disable-static --with-pic --with-layout=GNU --without-pear
  --enable-filter --with-openssl --with-libxml --enable-session --with-zlib)
extensions=(--enable-bcmath=shared --with-bz2=shared --enable-calendar=shared
  --enable-ctype=shared --with-curl=shared --enable-exif=shared --enable-fileinfo=shared --with-ffi=shared
  --enable-ftp=shared --enable-gd=shared --with-jpeg --with-freetype --with-webp
  --with-gettext=shared --with-gmp=shared --with-iconv=shared --enable-intl=shared
  --enable-json=shared --enable-mbstring=shared --enable-mysqlnd=shared
  --with-mysqli=shared,mysqlnd --enable-pdo=shared --with-pdo-mysql=shared,mysqlnd
  --with-pgsql=shared --with-pdo-pgsql=shared --enable-opcache --enable-pcntl
  --enable-phar=shared --enable-posix=shared --with-libedit=shared
  --enable-shmop=shared --enable-soap=shared --enable-sockets=shared
  --with-sodium=shared --with-sqlite3=shared --with-pdo-sqlite=shared
  --enable-sysvmsg=shared --enable-sysvsem=shared --enable-sysvshm=shared
  --enable-tokenizer=shared --enable-dom=shared --enable-simplexml=shared
  --enable-xml=shared --enable-xmlreader=shared --enable-xmlwriter=shared
  --with-xsl=shared --with-zip=shared)
mkdir /build/cli /build/fpm
cd /build/cli
/build/source/configure "${common[@]}" "${extensions[@]}" \
  --enable-cli --enable-cgi --disable-fpm --disable-phpdbg \
  --with-config-file-path=/etc/php/7.4/cli --with-config-file-scan-dir=/etc/php/7.4/cli/conf.d \
  > /out/evidence/configure-cli.log 2>&1 || { tail -100 /out/evidence/configure-cli.log; exit 1; }
make -j"${JOBS:-4}" > /out/evidence/make-cli.log 2>&1 || { tail -100 /out/evidence/make-cli.log; exit 1; }
cd /build/fpm
/build/source/configure "${common[@]}" --disable-cli --disable-cgi --disable-phpdbg \
  --enable-fpm --with-fpm-user=www-data --with-fpm-group=www-data \
  --sysconfdir=/etc/php/7.4/fpm \
  --with-fpm-systemd --with-fpm-acl --with-fpm-apparmor \
  --with-config-file-path=/etc/php/7.4/fpm --with-config-file-scan-dir=/etc/php/7.4/fpm/conf.d \
  > /out/evidence/configure-fpm.log 2>&1 || { tail -100 /out/evidence/configure-fpm.log; exit 1; }
make -j"${JOBS:-4}" > /out/evidence/make-fpm.log 2>&1 || { tail -100 /out/evidence/make-fpm.log; exit 1; }
python3 /repo/scripts/package.py
bash /repo/tests/phpt.sh
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /out/evidence/build-packages.tsv
echo "Build and source regression tests passed: $TARGET"
