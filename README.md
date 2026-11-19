# PHP 7.4 security backports for old Ubuntu and Debian

[![Build](https://github.com/Niek/php7/actions/workflows/build.yml/badge.svg)](https://github.com/Niek/php7/actions/workflows/build.yml)

**Still running PHP 7.4 on an old Ubuntu or Debian server?** These drop-in `.deb`
packages bring in the latest PHP 7.4 security fixes from
[Sury's packages](https://packages.sury.org/php/), including critical remote
code execution bugs such as **CVE-2026-109618**, **CVE-2026-109619** and
**CVE-2026-129496**, on Ubuntu and Debian releases outside standard support.

| Distribution | Supported releases (amd64) |
| ------------ | -------------------------------------------------------------- |
| Ubuntu       | 16.04, 16.10, 17.04, 17.10, 18.04, 18.10, 19.04, 19.10, 20.04 |
| Debian       | 9 (Stretch), 10 (Buster), 11 (Bullseye)                         |

> [!WARNING]
> PHP 7.4 is end-of-life; these OS releases are outside standard support.
> Use this to buy time for an upgrade, not as ongoing security support.

## Upgrade

You need Bash, `curl`, `xz-utils` and working APT sources for your release.
Back up your PHP configuration first, then run:

```bash
target=$(. /etc/os-release; echo "$ID$VERSION_ID")
cd "$(mktemp -d)"
curl -fL "https://github.com/Niek/php7/releases/latest/download/php7.4-$target-amd64.tar.xz" -o php7.4.tar.xz
tar -xJf php7.4.tar.xz
sha256sum -c SHA256SUMS
sudo apt install --only-upgrade ./*.deb
```

This detects your release (for example `ubuntu18.04` or `debian10`), checks
the package checksums, and upgrades only the PHP 7.4 packages you already have
installed, including extensions, the Apache module and FPM. APT may install
required dependencies. Review APT's proposed changes before accepting.

When it finishes, restart PHP-FPM, Apache or any other long-running PHP process.

## What changes

- **Fixed:** every security backport in Sury's PHP 7.4.33 revision 37, including:
  - CVE-2026-109618 and CVE-2026-109619 (remote code execution), using the
    [official upstream backports](https://github.com/php/php-src/archive/refs/heads/PHP-7.4-CVE-2026-109618-109619.zip)
  - CVE-2026-129496, CVE-2026-126714 and CVE-2026-115560 (remote code execution
    via the timezone cache and sessions)
  - CVE-2026-129538 (PHP-CGI out-of-bounds write) and CVE-2026-128090 (PHAR
    signature bypass)
  - CVE-2026-129289, CVE-2026-129291 and CVE-2026-129292 (PHP-FPM request
    smuggling, use-after-free and status page XSS)
  - CVE-2026-15353, CVE-2026-129506, CVE-2026-128064, CVE-2026-127960 and
    CVE-2024-11235 (SOAP, HTTP streams and request shutdown)
- **Disabled:** session upload-progress tracking, as part of the fix. Regular
  file uploads still work.
- **On releases with older libraries:** PCRE2 is bundled instead of using the
  system copy, and Argon2 password hashing may be unavailable.
- **Not included:** third-party extensions, such as those from PECL.

## How it's built

GitHub Actions downloads the pinned
[Sury PHP 7.4.33 source](https://github.com/Niek/php7/releases/latest/download/php7.4-source.tar.xz),
verifies it against `sources.sha256`, then builds it in Docker for each release
using that release's own libraries. Sury's packaging (extensions, FPM config and
services) is kept as-is. `build.sh` only adjusts what older toolchains need.
The PHP test suite is not run.

### Releasing

Every push and pull request builds all releases. To publish, set `REVISION` in
`.github/workflows/build.yml` and push the matching tag, for example
`v7.4.33-1`. The packages, build logs, checksums and source are attached to the
GitHub release once all builds succeed.
