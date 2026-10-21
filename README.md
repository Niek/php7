# php7

[![Build](https://github.com/Niek/php7/actions/workflows/build.yml/badge.svg)](https://github.com/Niek/php7/actions/workflows/build.yml)

PHP 7.4 `.deb` packages for **every Ubuntu release from 16.04 through 20.04**
(including 16.10, 17.04, 17.10, 18.10, 19.04 and 19.10) and **Debian 9/10**, amd64.
Built in Docker on `ubuntu-latest`, using each distribution's native libraries
and Sury's existing Debian packaging, including FPM configuration and services.

The pinned PHP 7.4.33 revision 31 source includes the official backports for
**CVE-2026-109618 and CVE-2026-109619**. Normal uploads remain available; the
backport disables session upload-progress tracking internally. Builds use bundled
PCRE2 or omit Argon2 where the target distribution lacks suitable native libraries.

Download packages for your **exact OS release** from [Releases](https://github.com/Niek/php7/releases),
verify `SHA256SUMS`, back up your installation, then install the matching `.deb`
files with APT. PHP 7.4 is EOL and these OS releases are outside normal support;
this is a bridge to upgrading, not a promise of continued security support.

Pushes and pull requests build the matrix. Push `v7.4.33-1` to publish packages,
build logs, checksums and corresponding source after all builds succeed. Increase
`REVISION` in the workflow for subsequent releases. No test suite is run.
