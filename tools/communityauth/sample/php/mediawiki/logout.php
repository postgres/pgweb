<?
require 'pgauth_conf.php';
/* Log the user out locally */

session_name('wikidb_session');
session_start();

unset($_SESSION['wsUserID']);
unset($_SESSION['wsToken']);
unset($_SESSION['wsUserName']);
setcookie('wikidbLoggedOut', time());

/* Redirect logout request too */
header("Location: https://www.postgresql.org/account/auth/${pgauth_siteid}/logout/");
?>
