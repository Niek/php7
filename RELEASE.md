PHP 7.4.33 with Sury revision 31 security backports, built for amd64 on Ubuntu
16.04 (xenial), Ubuntu 18.04 (bionic), and Debian 10 (buster).

Includes the official minimal backport for CVE-2026-109618 and CVE-2026-109619.
**Normal multipart uploads work; PHP session upload-progress tracking is disabled
internally by the backport.** Memory allocation failures exit the worker without
PHP shutdown handlers; FPM starts a replacement.

Download only the archive for your exact OS release. Verify SHA256SUMS and the
GitHub Actions attestation before installation. Each archive includes packages,
dependency/source manifests, tests, build logs and installation/rollback guidance.
Separate `.deb` files and corresponding source are also provided.

All targets must pass signature/source checks, compilation, focused upstream PHPTs,
clean-container package installation, library and extension checks, real FPM
multipart uploads, session tests, memory-exhaustion recovery and configuration
preservation before this release is published.

This initial set supplies CLI, FPM and common extensions; it does not include
Apache mod_php, CGI packages, phpdbg, development headers or PECL extensions.
Native library capabilities differ between distributions; Argon2 password hashing
is not included. Read the repository README before upgrading an existing custom
or third-party PHP installation. PHP 7.4 and the target operating systems remain
end of life; these packages are a migration bridge, not ongoing platform support.
