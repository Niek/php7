# php7

[![Build](https://github.com/Niek/php7/actions/workflows/build.yml/badge.svg)](https://github.com/Niek/php7/actions/workflows/build.yml)

PHP 7.4 `.deb` packages for **every Ubuntu release from 16.04 through 20.04**
(including 16.10, 17.04, 17.10, 18.10, 19.04 and 19.10) and **Debian 9/10**, amd64.
Built in Docker on `ubuntu-latest`, using each distribution's native libraries
and Sury's existing Debian packaging, including FPM configuration and services.

The pinned [Sury PHP 7.4.33 revision 31 source](https://github.com/Niek/php7/releases/latest/download/php7.4-source.tar.xz) includes the
[official PHP backports (source ZIP)](https://github.com/php/php-src/archive/refs/heads/PHP-7.4-CVE-2026-109618-109619.zip) for
**CVE-2026-109618 and CVE-2026-109619**. Normal uploads remain available; the
backport disables session upload-progress tracking internally. Builds use bundled
PCRE2 or omit Argon2 where the target distribution lacks suitable native libraries.

PHP 7.4 is EOL and these OS releases are outside normal support;
this is a bridge to upgrading, not a promise of continued security support.

## Upgrade

Back up your PHP configuration and packages first. In **Bash** on **amd64**, choose
your **exact OS release**, then run the upgrade block below. You need
`curl`, `xz-utils` and working APT sources for that release.

### Ubuntu 16.04 (Xenial)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu16.04-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 16.10 (Yakkety)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu16.10-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 17.04 (Zesty)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu17.04-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 17.10 (Artful)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu17.10-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 18.04 (Bionic)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu18.04-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 18.10 (Cosmic)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu18.10-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 19.04 (Disco)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu19.04-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 19.10 (Eoan)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu19.10-amd64.tar.xz -o php7.4.tar.xz
```

### Ubuntu 20.04 (Focal)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-ubuntu20.04-amd64.tar.xz -o php7.4.tar.xz
```

### Debian 9 (Stretch)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-debian9-amd64.tar.xz -o php7.4.tar.xz
```

### Debian 10 (Buster)

```bash
cd "$(mktemp -d)" &&
curl -fL https://github.com/Niek/php7/releases/latest/download/php7.4-debian10-amd64.tar.xz -o php7.4.tar.xz
```

### Upgrade installed packages

Run this in the same shell to upgrade existing PHP packages, including installed
extensions and Apache/FPM packages. Review APT's proposed changes before accepting.

```bash
tar -xJf php7.4.tar.xz
sha256sum -c SHA256SUMS
sudo apt install --only-upgrade ./*.deb
```

Restart any long-running PHP workers after upgrading. Third-party extensions are
not included in these bundles.

## Build and release

Pushes and pull requests build the matrix. Push `v7.4.33-1` to publish packages,
build logs, checksums and corresponding source after all builds succeed. Increase
`REVISION` in the workflow for subsequent releases. No test suite is run.
