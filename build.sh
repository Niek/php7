#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# shellcheck disable=SC1091
. /etc/os-release

if [ "$ID" = debian ]; then
  printf '%s\n' 'deb http://archive.debian.org/debian buster main' \
    'deb http://archive.debian.org/debian-security buster/updates main' > /etc/apt/sources.list
  echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99archive
fi
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod +x /usr/sbin/policy-rc.d
apt-get update
apt-get install -y --no-install-recommends build-essential devscripts equivs dpkg-dev ca-certificates

mkdir -p /build /out
cd /sources
sha256sum -c /repo/sources.sha256
dpkg-source --no-check -x ./*.dsc /build/php
cd /build/php

# Keep Sury's packaging, including extensions, FPM units, pools and maintainer
# scripts. Adjust only compatibility with the target's native build tools/libs.
sed -i 's/php-common (>= 1:81~)/php-common (>= 1:35)/g' debian/control debian/control.in debian/php-module.control.in
if [ "$VERSION_ID" = 16.04 ]; then
  apt-get install -y --no-install-recommends -t xenial-backports debhelper
  sed -i -e '/libargon2-dev | libargon2-0-dev,/d' \
    -e '/libpcre2-dev (>= 10.30),/d' \
    -e 's/libtidy-dev (>= 1:5.2.0)/libtidy-dev/' debian/control debian/control.in
  # Xenial has no Argon2 and its PCRE2 is too old; use PHP's bundled PCRE2.
  sed -i -e '/--with-password-argon2=/d' -e '/--with-external-pcre/d' debian/rules
fi

export DEB_BUILD_OPTIONS="nocheck parallel=${JOBS:-4}"
export DEB_BUILD_PROFILES=nocheck
export DEBFULLNAME='php7 contributors' DEBEMAIL='noreply@github.com'
dch --newversion "1:7.4.33-31+php7.${REVISION:-1}~${TARGET}.1" --distribution "${VERSION_CODENAME:-${UBUNTU_CODENAME:-buster}}" \
  'Rebuild Sury security backports for this distribution.'
mk-build-deps --install --remove --tool 'apt-get -y --no-install-recommends' debian/control
dpkg-buildpackage -us -uc -b -j"${JOBS:-4}"
cp /build/*.deb /out/
find /build -maxdepth 1 -type f \( -name '*.buildinfo' -o -name '*.changes' \) -exec cp {} /out/ \;
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /out/build-dependencies.txt
cd /out
sha256sum ./*.deb > SHA256SUMS
