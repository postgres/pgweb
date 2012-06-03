<?php
require 'pgauth_conf.php';

if ($_GET['s'] == "logout") {
  /*
   * Redirect back from the authentication system after a
   * distributed logout. Just send it back to the frontpage for now.
   */
  header("Location: ${pgauth_logoutsite}/");
  exit(0);
}

session_name('wikidb_session');
session_start();

$iv = $_GET['i'];
$d = $_GET['d'];

$key = base64_decode(strtr(${pgauth_key}, '-_', '+/'), true);
$iv = base64_decode(strtr($iv, '-_', '+/'), true);
$d = base64_decode(strtr($d, '-_', '+/'), true);
if ($key == FALSE || $iv == FALSE || $d == FALSE) {
  print "Invalid authentication data";
  exit(0);
}

$td = mcrypt_module_open("rijndael-128", "", "cbc", "");
if (!$td) {
  print "Unable to open mcrypt module";
  exit(0);
}

$r = mcrypt_generic_init($td, $key, $iv);
/* Docs say FALSE or <0 is incorrect. But it returns FALSE when it works.. */
if ($r < 0) {
  print "Unable to initialize encryption module: $r";
  exit(0);
}

$decrypted = rtrim(mdecrypt_generic($td, $d));
mcrypt_generic_deinit($td);
mcrypt_module_close($td);
parse_str($decrypted, $data);

if ($data['t'] < time() - 10) {
  print "Authentication token too old";
  exit(0);
}

// User found, and we read a reasonable authenticaiton time.
// Look for the user in the mediawiki database
$db = pg_connect(${pgauth_connstr});
$q = pg_query_params($db, "SELECT user_token, user_id, user_real_name, user_email FROM mwuser WHERE user_name=$1", array(ucfirst(strtolower($data['u']))));
if (pg_num_rows($q) == 0) {
  /*
   * Create a token the same way mediawiki does (ish).
   * We cheat on some points though, but that shouldn't
   * be an issue really - it's random enough.
   */
  $token = md5(microtime() . mt_rand(0, 0x7fffffff));

  /* Hardcoded default options.. Ugly, but it works.. */
  $options=<<<EOT
quickbar=1
underline=2
cols=80
rows=25
searchlimit=20
contextlines=5
contextchars=50
skin=postgresql
math=1
rcdays=7
rclimit=50
wllimit=250
highlightbroken=1
stubthreshold=0
previewontop=1
editsection=1
editsectiononrightclick=0
showtoc=1
showtoolbar=1
date=ISO 8601
imagesize=2
thumbsize=2
rememberpassword=0
enotifwatchlistpages=1
enotifusertalkpages=1
enotifminoredits=1
enotifrevealaddr=0
shownumberswatching=0
fancysig=0
externaleditor=0
externaldiff=0
showjumplinks=1
numberheadings=0
uselivepreview=0
watchlistdays=3
variant=
language=en
searchNs0=1
nickname=
timecorrection=
ajaxsearch=
searchNs1=0
searchNs2=0
searchNs3=0
searchNs4=0
searchNs5=0
searchNs6=0
searchNs7=0
searchNs8=0
searchNs9=0
searchNs10=0
searchNs11=0
searchNs12=0
searchNs13=0
searchNs14=0
searchNs15=0
disablemail=1
justify=0
hideminor=0
extendwatchlist=0
usenewrc=0
editondblclick=0
editwidth=0
watchcreations=0
watchdefault=0
watchmoves=0
watchdeletion=0
minordefault=0
previewonfirst=0
nocache=0
forceeditsummary=0
watchlisthideown=0
watchlisthidebots=0
watchlisthideminor=0
ccmeonemails=1
diffonly=0
EOT;

  /*
   * Try to create a user..
   */
  $q = pg_query_params($db, "INSERT INTO mwuser (user_name, user_real_name, user_password, user_newpassword, user_newpass_time, user_token, user_email, user_email_token, user_email_token_expires, user_email_authenticated, user_options, user_touched, user_registration, user_editcount, user_hidden) VALUES ($1, $2, NULL, NULL, NULL, $3, $4, NULL, '2000-01-01 00:00:00', CURRENT_TIMESTAMP, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0) RETURNING user_token, user_id, user_real_name, user_email", array(ucfirst(strtolower($data['u'])), $data['f'] . ' ' . $data['l'], $token, $data['e'], $options));
  if (pg_num_rows($q) != 1) {
    print "Failed to add user!";
    pg_close($db);
    exit(0);
  }
}
else if (pg_num_rows($q) != 1) {
  print "Invalid data returned!";
  pg_close($db);
  exit(0);
}

/*
 * Update email and real name, if they changed in the community
 * auth system. Community auth always overwrites whatever is
 * in the wiki.
 */
$r = pg_fetch_assoc($q);
if ($r['user_email'] != $data['e']) {
  $q = pg_query_params($db, "UPDATE mwuser SET user_email=$1 WHERE user_name=$2", array($data['e'], ucfirst(strtolower($data['u']))));
  if (pg_result_status($q) != PGSQL_COMMAND_OK) {
    print "Failed to update email!";
    pg_close($db);
    exit(0);
  }
}
if ($r['user_real_name'] != $data['f'] . ' ' . $data['l']) {
  $q = pg_query_params($db, "UPDATE mwuser SET user_real_name=$1 WHERE user_name=$2", array($data['f'] . ' ' . $data['l'], ucfirst(strtolower($data['u']))));
  print "'$q'";
  if (pg_result_status($q) != PGSQL_COMMAND_OK) {
    print "Failed to update real name!";
    pg_close($db);
    exit(0);
  }
}

pg_close($db);

// Now inject this data into the mediawiki session
$_SESSION['wsUserID'] = $r['user_id'];
$_SESSION['wsToken'] = $r['user_token'];
$_SESSION['wsUserName'] = ucfirst(strtolower($data['u']));
session_write_close();

if ($data['su']) {
  $redir = $data['su'];
} else {
  $redir = '/wiki/Main_Page';
}

/* Add ?nocache=... or &nocache=... to avoid mediawiki caching */
$redir .= strpos($redir, "?")==false?"?":"&";
$redir .= "nocache=" . urlencode(microtime());
header("Location: ${pgauth_rootsite}$redir");
header("Cache-control: private, must-revalidate, max-age=0");
?>
