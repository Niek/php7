#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
. /etc/os-release
case "$TARGET:$ID:$VERSION_ID:$(dpkg --print-architecture)" in
  ubuntu16.04:ubuntu:16.04:amd64|ubuntu18.04:ubuntu:18.04:amd64) ;;
  debian10:debian:10:amd64)
    cat > /etc/apt/sources.list <<'EOF'
deb http://archive.debian.org/debian buster main
deb http://archive.debian.org/debian-security buster/updates main
EOF
    # Archived metadata has expired; signatures remain mandatory.
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99archive
    ;;
  *) echo "Wrong distro/architecture for $TARGET" >&2; exit 1 ;;
esac
apt-get -o Acquire::Retries=3 update
# Containers have no service manager. Maintainer scripts must respect this.
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
