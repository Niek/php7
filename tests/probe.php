<?php
header('Content-Type: application/json');
if (isset($_GET['oom'])) {
    register_shutdown_function(function () { file_put_contents(__DIR__.'/state/shutdown', 'unsafe'); });
    $a = str_repeat('x', 128 * 1024 * 1024);
    exit('OOM did not occur');
}
session_start();
$progress = array_filter(array_keys($_SESSION), function ($k) { return strpos($k, 'upload_progress_') === 0; });
$_SESSION['counter'] = ($_SESSION['counter'] ?? 0) + 1;
$result = ['pid' => getmypid(), 'method' => $_SERVER['REQUEST_METHOD'],
           'counter' => $_SESSION['counter'], 'progress' => array_values($progress),
           'progress_ini' => ini_get('session.upload_progress.enabled'),
           'body_length' => strlen(file_get_contents('php://input'))];
if (isset($_FILES['upload'])) {
    $f = $_FILES['upload'];
    $result['error'] = $f['error'];
    $result['uploaded'] = is_uploaded_file($f['tmp_name']);
    $result['sha256'] = hash_file('sha256', $f['tmp_name']);
    $result['moved'] = move_uploaded_file($f['tmp_name'], __DIR__.'/state/uploaded');
    unlink(__DIR__.'/state/uploaded');
}
session_write_close();
echo json_encode($result);
