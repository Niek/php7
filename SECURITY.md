# Security scope

This project distributes reviewed source backports for the exact package/OS
combinations in the README. PHP 7.4 and these distributions are end of life.
There is no promise of comprehensive vulnerability coverage, future backports,
or a security response deadline. Prefer migrating to a supported OS and PHP.

The initial source is Sury PHP 7.4.33 revision 31, with 164 patches including the
official minimal backport for CVE-2026-109618 and CVE-2026-109619. The patch disables
session upload-progress tracking internally and exits the process on allocation
failure. It does not fix unrelated vulnerabilities in the OS, its libraries,
third-party extensions or applications. Passing tests establish the documented
checks, not the absence of all vulnerabilities.

Download only exact-target releases from this repository. Check SHA256 hashes and
GitHub Actions attestations. Review the source lock, signed provenance, package
dependencies and test evidence. Run builds on disposable workers. Keep release
credentials out of builds and untrusted pull requests.

Report an undisclosed vulnerability through GitHub's private vulnerability
reporting feature on this repository. Do not put secrets, production configuration,
or an undisclosed exploit in a public issue. Reproducible non-sensitive build and
packaging problems can be filed as ordinary issues.
