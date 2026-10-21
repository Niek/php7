#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
# shellcheck disable=SC1091
. /etc/os-release
codename=${VERSION_CODENAME:-${UBUNTU_CODENAME:-}}

if [ "$ID" = debian ]; then
  [ "$VERSION_ID" != 9 ] || codename=stretch
  printf '%s\n' "deb http://archive.debian.org/debian $codename main" \
    "deb http://archive.debian.org/debian-security $codename/updates main" > /etc/apt/sources.list
  echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99archive
else
  case "$VERSION_ID" in
    16.04|18.04|20.04) ;;
    *)
      for pocket in "$codename" "$codename-updates" "$codename-security" "$codename-backports"; do
        echo "deb http://old-releases.ubuntu.com/ubuntu $pocket main universe restricted multiverse"
      done > /etc/apt/sources.list
      ;;
  esac
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
fi
# Use bundled PCRE2 where the distro predates PHP 7.4's required library API.
pcre_version=$(apt-cache policy libpcre2-dev | awk '/Candidate:/ {print $2}')
if dpkg --compare-versions "$pcre_version" lt 10.30; then
  sed -i '/libpcre2-dev (>= 10.30),/d' debian/control debian/control.in
  sed -i '/--with-external-pcre/d' debian/rules
fi
if ! apt-cache policy libargon2-dev libargon2-0-dev | awk '/Candidate:/ && $2 != "(none)" {found=1} END {exit !found}'; then
  sed -i '/libargon2-dev | libargon2-0-dev,/d' debian/control debian/control.in
  sed -i '/--with-password-argon2=/d' debian/rules
fi
# PHP also supports legacy HTML Tidy, detected by its configure script.
sed -i 's/libtidy-dev (>= 1:5.2.0)/libtidy-dev/' debian/control debian/control.in

export DEB_BUILD_OPTIONS="nocheck parallel=${JOBS:-4}"
export DEB_BUILD_PROFILES=nocheck
export DEBFULLNAME='php7 contributors' DEBEMAIL='noreply@github.com'
dch --newversion "1:7.4.33-31+php7.${REVISION:-1}~${TARGET}.1" --distribution "$codename" \
  'Rebuild Sury security backports for this distribution.'
mk-build-deps --install --remove --tool 'apt-get -y --no-install-recommends' debian/control
dpkg-buildpackage -us -uc -b -j"${JOBS:-4}"
cp /build/*.deb /out/
find /build -maxdepth 1 -type f \( -name '*.buildinfo' -o -name '*.changes' \) -exec cp {} /out/ \;
dpkg-query -W -f='${binary:Package}\t${Version}\n' > /out/build-dependencies.txt
cd /out
sha256sum ./*.deb > SHA256SUMS
