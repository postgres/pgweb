<?
require 'pgauth_conf.php';
/* Redirect authentication request */

$su = "/wiki/" . $_GET['r'];
header("Location: https://www.postgresql.org/account/auth/${pgauth_siteid}/?su=" . urlencode($su));
?>
