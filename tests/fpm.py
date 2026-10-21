#!/usr/bin/env python3
"""Exercise actual multipart parsing, session state and OOM worker replacement."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import struct
import subprocess
import tempfile
import time

root = Path(tempfile.mkdtemp(prefix='php7-fpm-'))
root.chmod(0o755)
(root / 'state').mkdir(mode=0o700)
os.chown(str(root / 'state'), 33, 33)
shutil.copyfile('/repo/tests/probe.php', str(root / 'probe.php'))
(root / 'probe.php').chmod(0o644)
sock = str(root / 'fpm.sock')
(root / 'fpm.conf').write_text('''[global]
daemonize = no
error_log = {root}/fpm.log
[test]
user = www-data
group = www-data
listen = {sock}
pm = static
pm.max_children = 1
catch_workers_output = yes
php_admin_value[memory_limit] = 16M
php_admin_value[session.save_path] = {root}/state
php_admin_value[session.upload_progress.enabled] = 1
php_admin_value[session.upload_progress.cleanup] = 0
php_admin_value[session.upload_progress.freq] = 1%
php_admin_value[session.upload_progress.min_freq] = 0
php_admin_value[max_input_vars] = 10000
'''.format(root=root, sock=sock))
log = open('/out/evidence/fpm-process.log', 'w')
process = subprocess.Popen(['php-fpm7.4', '-F', '-y', str(root / 'fpm.conf')],
                           stdout=log, stderr=subprocess.STDOUT, preexec_fn=os.setsid)

def record(kind, data=b''):
    return struct.pack('!BBHHBB', 1, kind, 1, len(data), 0, 0) + data

def length(n):
    return bytes([n]) if n < 128 else struct.pack('!I', n | 0x80000000)

def request(method='GET', body=b'', content_type='', query=''):
    params = {'GATEWAY_INTERFACE': 'CGI/1.1', 'SERVER_PROTOCOL': 'HTTP/1.1',
              'SERVER_SOFTWARE': 'php7-test', 'SERVER_NAME': 'localhost',
              'SERVER_ADDR': '127.0.0.1', 'SERVER_PORT': '80', 'REMOTE_ADDR': '127.0.0.1',
              'SCRIPT_FILENAME': str(root / 'probe.php'), 'SCRIPT_NAME': '/probe.php',
              'REQUEST_URI': '/probe.php' + ('?' + query if query else ''),
              'REQUEST_METHOD': method, 'QUERY_STRING': query,
              'CONTENT_TYPE': content_type, 'CONTENT_LENGTH': str(len(body)),
              'HTTP_COOKIE': 'PHPSESSID=php7regressiontest'}
    encoded = b''
    for k, v in params.items():
        k, v = k.encode(), v.encode()
        encoded += length(len(k)) + length(len(v)) + k + v
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(20)
    connection.connect(sock)
    connection.sendall(record(1, struct.pack('!HB5x', 1, 0)) + record(4, encoded) + record(4))
    try:
        for start in range(0, len(body), 65535):
            connection.sendall(record(5, body[start:start+65535]))
        connection.sendall(record(5))
        received = b''
        while True:
            chunk = connection.recv(65536)
            if not chunk:
                break
            received += chunk
    except (BrokenPipeError, ConnectionResetError):
        received = b''
    finally:
        connection.close()
    stdout = b''
    while len(received) >= 8:
        _, kind, _, size, padding, _ = struct.unpack('!BBHHBB', received[:8])
        if kind == 6:
            stdout += received[8:8+size]
        received = received[8+size+padding:]
    if b'\r\n\r\n' not in stdout:
        return None
    headers, response = stdout.split(b'\r\n\r\n', 1)
    if b'Status: 500' in headers or not response:
        return None
    return json.loads(response.decode())

try:
    for _ in range(200):
        if Path(sock).exists():
            break
        assert process.poll() is None, 'FPM exited at startup'
        time.sleep(0.05)
    first = request()
    assert first['counter'] == 1, first
    payload = b'php7 multipart verification\x00\xff\n' * 10000
    boundary = 'php7-boundary-813944'
    body = ('--' + boundary + '\r\nContent-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"\r\n\r\ncheck\r\n'
            '--' + boundary + '\r\nContent-Disposition: form-data; name="upload"; filename="test.bin"\r\n'
            'Content-Type: application/octet-stream\r\n\r\n').encode() + payload + ('\r\n--' + boundary + '--\r\n').encode()
    ctype = 'multipart/form-data; boundary=' + boundary
    uploaded = request('POST', body, ctype)
    assert uploaded['error'] == 0 and uploaded['uploaded'] and uploaded['moved'], uploaded
    assert uploaded['sha256'] == hashlib.sha256(payload).hexdigest(), uploaded
    assert uploaded['counter'] == 2 and uploaded['progress_ini'] == '1', uploaded
    assert uploaded['progress'] == [], 'EOL security patch must suppress progress records'
    assert 'upload_progress_' not in (root / 'state/sess_php7regressiontest').read_text()
    for method in ('PUT', 'PATCH'):
        response = request(method, body, ctype)
        assert response['method'] == method and response['body_length'] == len(body), response
    old_pid = request()['pid']
    assert request(query='oom=1') is None, 'OOM unexpectedly completed'
    time.sleep(0.3)
    healthy = request()
    assert healthy['pid'] != old_pid and healthy['counter'] >= 5, healthy
    assert not (root / 'state/shutdown').exists(), 'OOM ran unsafe PHP shutdown handler'
    # Force allocation failure while constructing nested input arrays, before the
    # application runs. The patched worker must exit and FPM must recover.
    nested = '&'.join('x{0}{1}=1'.format(i, '[a]' * 60) for i in range(2000)).encode()
    assert request('POST', nested, 'application/x-www-form-urlencoded') is None
    time.sleep(0.3)
    final = request('POST', body, ctype)
    assert final['pid'] != healthy['pid'] and final['moved'], final
    assert final['sha256'] == hashlib.sha256(payload).hexdigest()
    print(json.dumps({'multipart_upload': 'PASS', 'sha256': final['sha256'],
                      'put_patch': 'PASS', 'session_persistence': 'PASS',
                      'upload_progress_disabled_internally': 'PASS',
                      'oom_worker_replacement': 'PASS', 'input_parser_oom_recovery': 'PASS'}, indent=2))
finally:
    os.killpg(process.pid, signal.SIGTERM)
    process.wait(timeout=10)
    log.close()
    if (root / 'fpm.log').exists():
        shutil.copyfile(str(root / 'fpm.log'), '/out/evidence/fpm.log')
    shutil.rmtree(str(root))
