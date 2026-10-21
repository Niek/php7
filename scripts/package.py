#!/usr/bin/env python3
"""Small Debian packager; compiled libraries are resolved in the target distro."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

repo, source = Path('/repo'), Path('/build/source')
lock = json.loads((repo / 'sources.lock.json').read_text())
target = os.environ['TARGET']
version = lock['package_version'] + '~' + target + '.1'
roots = Path('/build/packages')
groups = {
    'common': 'calendar ctype exif fileinfo ffi ftp gettext iconv pdo phar posix shmop sockets sodium sysvmsg sysvsem sysvshm tokenizer',
    'bcmath': 'bcmath', 'bz2': 'bz2', 'curl': 'curl', 'gd': 'gd', 'gmp': 'gmp',
    'intl': 'intl', 'json': 'json', 'mbstring': 'mbstring',
    'mysql': 'mysqlnd mysqli pdo_mysql', 'opcache': 'opcache',
    'pgsql': 'pgsql pdo_pgsql', 'readline': 'readline', 'soap': 'soap',
    'sqlite3': 'sqlite3 pdo_sqlite', 'xml': 'dom simplexml xml xmlreader xmlwriter xsl',
    'zip': 'zip', 'cli': '', 'fpm': '',
}
priorities = {'pdo': 10, 'opcache': 10, 'mysqlnd': 10, 'xml': 15}

def write(root, name, content, mode=0o644):
    path = root / name.lstrip('/')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(mode)

def copy(root, src, dest, executable=False):
    path = root / dest.lstrip('/')
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(str(src), str(path))
    path.chmod(0o755 if executable else 0o644)

# shlibdeps needs a minimal source control file, but no current Debian build
# tooling or foreign binary libraries enter the target container.
control = Path('/build/debian/control')
control.parent.mkdir(exist_ok=True)
control.write_text('Source: php7.4\nSection: php\nPriority: optional\n'
                   'Maintainer: php7 contributors <noreply@github.com>\n\n'
                   'Package: php7.4\nArchitecture: any\nDescription: PHP 7.4\n')
manifest = {'target': target, 'architecture': 'amd64', 'version': version,
            'source_revision': os.environ['SOURCE_REVISION'], 'source': lock,
            'image': json.loads((repo / 'targets.json').read_text())[target]['image'],
            'upload_progress': 'disabled internally by official EOL backport',
            'packages': {}}
for suffix, module_string in sorted(groups.items()):
    package = 'php7.4-' + suffix
    modules = module_string.split()
    root = roots / package
    root.mkdir(parents=True, exist_ok=True)
    binaries = []
    for module in modules:
        path = '/usr/lib/php/20190902/' + module + '.so'
        copy(root, Path('/build/cli/modules') / (module + '.so'), path, True)
        binaries.append(root / path.lstrip('/'))
        directive = 'zend_extension' if module == 'opcache' else 'extension'
        ini = '; priority={0}\n{1}={2}.so\n'.format(priorities.get(module, 20), directive, module)
        write(root, '/usr/share/' + package + '/' + module + '.ini', ini)
    if suffix in ('cli', 'fpm'):
        for directory in ('/etc/php/7.4/' + suffix + '/conf.d',):
            (root / directory.lstrip('/')).mkdir(parents=True, exist_ok=True)
        if suffix == 'cli':
            path = '/usr/bin/php7.4'
            copy(root, '/build/cli/sapi/cli/php', path, True)
        else:
            path = '/usr/sbin/php-fpm7.4'
            copy(root, '/build/fpm/sapi/fpm/php-fpm', path, True)
            copy(root, repo / 'packaging/php7.4-fpm.service', '/lib/systemd/system/php7.4-fpm.service')
            copy(root, repo / 'packaging/php7.4-fpm.init', '/etc/init.d/php7.4-fpm', True)
            copy(root, repo / 'packaging/php-fpm.conf', '/etc/php/7.4/fpm/php-fpm.conf')
            copy(root, repo / 'packaging/www.conf', '/etc/php/7.4/fpm/pool.d/www.conf')
            write(root, 'DEBIAN/conffiles', '/etc/init.d/php7.4-fpm\n/etc/php/7.4/fpm/php-fpm.conf\n/etc/php/7.4/fpm/pool.d/www.conf\n')
            write(root, 'DEBIAN/triggers', 'interest-noawait php7.4-fpm-restart\n')
        binaries.append(root / path.lstrip('/'))
        ini = (source / 'php.ini-production').read_text()
        ini += '\n; Debian session storage\nsession.save_path = "/var/lib/php/sessions"\n'
        if suffix == 'cli':
            ini += 'memory_limit = -1\n'
        write(root, '/usr/share/' + package + '/php.ini', ini)
    for binary in binaries:
        subprocess.check_call(['strip', '--strip-unneeded', str(binary)])
    command = ['dpkg-shlibdeps', '-O'] + ['-e' + str(p) for p in binaries]
    dependencies = subprocess.check_output(command, cwd='/build', universal_newlines=True).strip()
    dependencies = dependencies.split('shlibs:Depends=', 1)[1] if dependencies else ''
    depends = [dependencies] if dependencies else []
    depends += ['php-common', 'ucf'] if suffix == 'common' else ['php7.4-common (= ' + version + ')']
    if suffix in ('cli', 'fpm'):
        depends += ['php7.4-json (= ' + version + ')']
    if suffix == 'fpm':
        depends += ['init-system-helpers', 'lsb-base']
    provides = '\nProvides: phpapi-20190902' if suffix in ('cli', 'fpm') else ''
    write(root, 'DEBIAN/control',
          'Package: {0}\nVersion: {1}\nArchitecture: amd64\nSection: php\nPriority: optional\n'
          'Maintainer: php7 contributors <noreply@github.com>\n'
          'Homepage: https://github.com/Niek/php7\nDepends: {2}{3}\n'
          'Description: PHP 7.4 {4} with reviewed security backports\n'
          ' Built for {5}. PHP 7.4 and this operating system remain end of life.\n'
          .format(package, version, ', '.join(depends), provides, suffix, target))
    post = '#!/bin/sh\nset -e\nif [ "$1" = configure ]; then\n'
    post += '  install -d /etc/php/7.4/mods-available\n'
    for module in modules:
        dest = '/etc/php/7.4/mods-available/' + module + '.ini'
        post += '  UCF_FORCE_CONFFOLD=1 ucf /usr/share/{0}/{1}.ini {2}\n  ucfr --force {0} {2}\n'.format(package, module, dest)
        post += '  phpenmod -m -v 7.4 -s ALL {0}\n'.format(module)
    if suffix in ('cli', 'fpm'):
        dest = '/etc/php/7.4/' + suffix + '/php.ini'
        post += '  UCF_FORCE_CONFFOLD=1 ucf /usr/share/{0}/php.ini {1}\n  ucfr --force {0} {1}\n'.format(package, dest)
        post += '  for ini in /etc/php/7.4/mods-available/*.ini; do\n    [ -f "$ini" ] || continue\n    module=${ini##*/}\n    phpenmod -m -v 7.4 -s ' + suffix + ' "${module%.ini}"\n  done\n'
    if suffix == 'common':
        post += '  install -d -m 1733 /var/lib/php/sessions\n'
    if suffix == 'cli':
        post += '  update-alternatives --install /usr/bin/php php /usr/bin/php7.4 74\n'
    post += 'fi\n'
    if suffix == 'fpm':
        post += '''if [ "$1" = configure ] || [ "$1" = triggered ]; then
  php-fpm7.4 --test
  if [ -d /run/systemd/system ]; then
    systemctl daemon-reload
  fi
  # Restart an existing service; do not enable/start a previously disabled one.
  invoke-rc.d php7.4-fpm try-restart
fi
'''
    else:
        post += 'if [ "$1" = configure ]; then dpkg-trigger --no-await php7.4-fpm-restart; fi\n'
    write(root, 'DEBIAN/postinst', post, 0o755)
    prerm = '#!/bin/sh\nset -e\n'
    if suffix == 'cli':
        prerm += 'if [ "$1" = remove ]; then update-alternatives --remove php /usr/bin/php7.4; fi\n'
    if suffix == 'fpm':
        prerm += 'if [ "$1" = remove ]; then invoke-rc.d php7.4-fpm stop; fi\n'
    write(root, 'DEBIAN/prerm', prerm, 0o755)
    purge = '#!/bin/sh\nset -e\nif [ "$1" = purge ]; then\n'
    for module in modules:
        purge += '  if command -v phpdismod >/dev/null; then phpdismod -m -v 7.4 -s ALL {0}; fi\n'.format(module)
    paths = ['/etc/php/7.4/mods-available/' + m + '.ini' for m in modules]
    if suffix in ('cli', 'fpm'):
        paths.append('/etc/php/7.4/' + suffix + '/php.ini')
    for path in paths:
        purge += '  rm -f {0}\n  if command -v ucf >/dev/null; then ucf --purge {0}; ucfr --purge {1} {0}; fi\n'.format(path, package)
    purge += 'fi\n'
    write(root, 'DEBIAN/postrm', purge, 0o755)
    copy(root, source / 'debian/copyright', '/usr/share/doc/' + package + '/copyright')
    copy(root, source / 'LICENSE', '/usr/share/doc/' + package + '/PHP-LICENSE')
    write(root, '/usr/share/doc/' + package + '/build.json', json.dumps(manifest, indent=2) + '\n')
    checksums = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and 'DEBIAN' not in path.parts:
            checksums.append(hashlib.md5(path.read_bytes()).hexdigest() + '  ' + str(path.relative_to(root)))
    write(root, 'DEBIAN/md5sums', '\n'.join(checksums) + '\n')
    destination = Path('/out/packages') / (package + '_' + version.replace('1:', '') + '_amd64.deb')
    subprocess.check_call(['dpkg-deb', '-Zxz', '--build', str(root), str(destination)])
    manifest['packages'][package] = {'filename': destination.name, 'depends': depends,
                                     'modules': modules, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
Path('/out/manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
