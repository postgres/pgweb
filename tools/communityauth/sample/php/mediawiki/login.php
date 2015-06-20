<?php
require 'pgauth_conf.php';
/* Redirect authentication request */

$d = base64_encode("/wiki/" . $_GET['r']);
header("Location: https://www.postgresql.org/account/auth/${pgauth_siteid}/?d=" . urlencode($d));
?>
