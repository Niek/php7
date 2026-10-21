# php7

[![Build and release](https://github.com/Niek/php7/actions/workflows/build.yml/badge.svg)](https://github.com/Niek/php7/actions/workflows/build.yml)

PHP 7.4 security-backport `.deb` packages for older Ubuntu and Debian systems.
A small build repository: pinned public source, Docker builds on GitHub's
`ubuntu-latest` runner, clean-container tests, and downloadable releases.

**This is a migration bridge, not continued support for PHP 7.4 or an EOL OS.**
The first release contains Sury's 164 patches through revision 31, including the
[official PHP 7.4 backport](https://github.com/php/php-src/commit/712e60f9edfd03f0960fc4fc3c2c375f42b90aa2)
for **CVE-2026-109618 and CVE-2026-109619**.

**Normal multipart uploads work. PHP's session upload-progress tracking is
disabled internally by that official backport, even when its INI setting says
On.** Allocation failures terminate the PHP worker without running PHP shutdown
handlers; FPM starts a replacement. Applications relying on either behavior
need testing before an upgrade.

## Targets

| OS | Codename | Architecture | PHP |
| --- | --- | --- | --- |
| Ubuntu 16.04 | xenial | amd64 | 7.4.33 + backports |
| Ubuntu 18.04 | bionic | amd64 | 7.4.33 + backports |
| Debian 10 | buster | amd64 | 7.4.33 + backports |

Every target is compiled and tested in its own digest-pinned Docker image against
that distribution's native libraries. No private server snapshots, foreign-release
binary packages, or repository-release switching are used. Archived Debian APT
metadata needs an expiry exception; APT signature checking stays enabled.

Native libraries remain as old as the target distribution. Features vary with
them: for example Xenial's libzip lacks ZIP encryption and its libsodium has fewer
functions than newer versions. Argon2 password hashing is not enabled in this first
build set. Moving from a third-party build with newer libraries can therefore
remove features even though the PHP extension ABI stays `20190902`.

## Download and install

Get the archive for your **exact OS release and architecture** from
[Releases](https://github.com/Niek/php7/releases). Each archive contains the `.deb`
set, dependency manifest, build/test evidence, installer and these instructions.
Source archives, signed source-index evidence and SHA256 checksums are also
published. The PHP CLI still reports `7.4.33`; use `dpkg-query -W 'php7.4*'` to
identify the backported package revision.

1. Download the matching archive and `SHA256SUMS`. Check the downloaded file with
   `sha256sum --ignore-missing -c SHA256SUMS`. On a modern machine with GitHub CLI,
   verify its Actions provenance with
   `gh attestation verify <archive.tar.xz> --repo Niek/php7`.
2. Take a VM snapshot or equivalent full backup. Test in a copy of your application,
   especially custom extensions, databases, jobs and any changed library features.
3. Extract the archive, enter its directory and install the native `python3` and
   `dpkg-repack` packages if they are missing. Run `sudo bash install.sh`.
4. Check `php7.4 -m`, `php-fpm7.4 --test`, service status, logs, actual application
   requests and an actual file upload. Restart long-running PHP queue workers and
   other PHP processes too. For a **new installation**, enable/start FPM explicitly
   with `sudo systemctl enable --now php7.4-fpm` and configure your web server to use
   `/run/php/php7.4-fpm.sock`.

The installer verifies the target and package hashes, simulates APT installation,
rejects removals and downgrades, and saves original PHP packages, configuration,
extension binaries and a package inventory under `/var/backups/php7-<timestamp>/`.
It preserves existing PHP INIs, pools, custom `conf.d` files, administrator-disabled
modules and systemd overrides. Active FPM is restarted; a disabled service stays
disabled. Existing vendor service-unit defaults are replaced by this package's
unit, so review any changes made directly to `/lib/systemd/system` beforehand.

The initial package set includes `cli`, `fpm`, `common`, `bcmath`, `bz2`, `curl`,
`gd`, `gmp`, `intl`, `json`, `mbstring`, `mysql`, `opcache`, `pgsql`, `readline`,
`soap`, `sqlite3`, `xml` and `zip`. Common modules include PDO, FFI, sodium, sockets
and the standard shared extensions. **Apache mod_php, CGI packages, phpdbg,
development headers and PECL extensions are not supplied.** The installer refuses
an installed `php7.4-*` package that this release does not replace. Custom/PECL
extensions require a separately reviewed upgrade path; ABI alone is not a
compatibility guarantee. There is no signed APT repository yet.

Do not remove multipart or upload-progress workarounds until **every backend they
protect** is patched and verified. This installer does not change Nginx or remove
existing workarounds. If upload-progress was explicitly disabled by configuration,
removing that setting cannot restore progress tracking with this minimal backport.

### Rollback

Prefer restoring the VM snapshot. For a package rollback, first restore the
security workarounds appropriate to the vulnerable version, then install the
saved `.deb` files from the backup's `packages/` directory using `dpkg -i`.
Restore `config-and-extensions.tar.gz` to `/`, validate FPM and your web server,
and restart the affected services and workers. Keep the new release archive too.
The backup does not contain databases, application data, all system libraries, or
arbitrary process-manager configuration; it is not a replacement for a full backup.

## Build locally

Requirements: Git, Python 3, GnuPG (`gpgv`), Docker, and internet access. The Docker
host can run a modern OS; the build and runtime test run inside the old target OS.
On ARM hosts Docker must provide amd64 emulation. Native amd64 CI is faster.

```sh
git clone https://github.com/Niek/php7.git
cd php7
python3 scripts/verify-origin.py
python3 scripts/run.py ubuntu16.04
python3 scripts/run.py ubuntu18.04
python3 scripts/run.py debian10
```

`JOBS=4` is the default. Each `docker run` uses `--rm`; source trees, build objects
and temporary containers disappear on completion. Downloaded source is cached in
`.cache/sources/`. Packages, configuration logs, build dependency versions, PHPT
results, runtime checks and the release bundle remain under `out/<target>/`.
Use `--stage build` or `--stage test` to run a stage independently.

The source lock and Docker image digests make inputs reviewable. Native APT packages
are not snapshot-pinned, and compiler output/build paths have not been proven
bit-for-bit reproducible. Exact installed build-library versions are retained in
each bundle. Source signatures authenticate the pinned Sury source; GitHub
attestations identify the workflow that built the distributed archives.

## CI and releases

Pushes to `main`, pull requests and manual dispatch build the full matrix.
Each job performs:

- Signature verification of the retained Sury index and SHA256 verification of all
  source archives; application and checking of all 164 patches.
- Separate CLI and FPM builds with the correct default INI paths, plus standard
  Debian package dependencies derived by `dpkg-shlibdeps`.
- Focused upstream PHPT regression tests. Upload-progress PHPTs are excluded
  because the official backport disables that feature; a direct test verifies
  its absence with the INI setting enabled and cleanup disabled.
- Installation in a fresh target container without compilers or development
  libraries; library resolution and functional extension checks.
- Actual FastCGI multipart upload/hash/move, PUT/PATCH requests, session
  persistence, PHP-level and input-parser memory exhaustion, worker replacement,
  and configuration/module-state preservation on reinstallation.

To publish, update the reviewed source lock and release notes, wait for `main` CI,
then push the exact tag named in `sources.lock.json`. The tag rebuilds the entire
matrix. Only after every job passes does one release job attest and upload all
assets, then publish the draft. Pull requests have no release credentials.

For a source update, verify the new official patches and signed repository index,
refresh `packaging/provenance/` and the SHA256 lock, increment the Debian package
revision and release tag, review regression failures, then run the entire matrix.
Never replace a published release silently. Do not claim a CVE is fixed based
only on a PHP version string or a successful compilation.

## Licensing and scope

Original build/packaging/test code is MIT licensed. PHP and the Sury patch set
retain their upstream licenses; corresponding source and notices are shipped.
This project is independent of PHP, Debian, Ubuntu and Sury. See [SECURITY.md](SECURITY.md)
for the security scope and reporting policy.
