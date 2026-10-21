<?php
function check($ok, $name) {
    if (!$ok) { throw new RuntimeException($name); }
    echo "PASS ", $name, "\n";
}
$manifest = json_decode(file_get_contents('/out/manifest.json'), true);
foreach ($manifest['packages'] as $package) {
    foreach ($package['modules'] as $module) {
        check(extension_loaded($module === 'opcache' ? 'Zend OPcache' : $module), 'module '.$module);
    }
}
check(PHP_VERSION === '7.4.33', 'version');
check(json_decode(json_encode(['a'=>42]), true)['a'] === 42, 'JSON');
check(bcadd('12345678901234567890', '1') === '12345678901234567891', 'BCMath');
check(gmp_strval(gmp_add('12345678901234567890', 1)) === '12345678901234567891', 'GMP');
check(mb_strlen('héllo', 'UTF-8') === 5, 'mbstring');
check(Normalizer::normalize("e\xCC\x81") === "\xC3\xA9", 'ICU normalization');
check(openssl_digest('php7', 'sha256') === hash('sha256', 'php7'), 'OpenSSL');
check(curl_version()['version'] !== '', 'curl');
check(password_verify('test', password_hash('test', PASSWORD_BCRYPT)), 'password hashing');
$key = random_bytes(SODIUM_CRYPTO_SECRETBOX_KEYBYTES);
$nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
check(sodium_crypto_secretbox_open(sodium_crypto_secretbox('hello', $nonce, $key), $nonce, $key) === 'hello', 'sodium');
$db = new PDO('sqlite::memory:');
check((int)$db->query('SELECT 42')->fetchColumn() === 42, 'PDO SQLite');
check(in_array('mysql', PDO::getAvailableDrivers()) && in_array('pgsql', PDO::getAvailableDrivers()), 'database drivers');
check(simplexml_load_string('<root>hello</root>')->__toString() === 'hello', 'XML');
$im = imagecreatetruecolor(10, 10);
ob_start(); imagepng($im); $png = ob_get_clean();
check(substr($png, 0, 8) === "\x89PNG\r\n\x1a\n", 'GD PNG');
$file = tempnam(sys_get_temp_dir(), 'php7-zip');
$zip = new ZipArchive();
check($zip->open($file, ZipArchive::OVERWRITE) === true, 'ZIP create');
$zip->addFromString('test', 'php7'); $zip->close();
check($zip->open($file) === true && $zip->getFromName('test') === 'php7', 'ZIP read');
$zip->close(); unlink($file);
check(bzdecompress(bzcompress('php7')) === 'php7', 'bzip2');
echo "All extension smoke tests passed.\n";
