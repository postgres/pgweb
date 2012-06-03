#!/usr/bin/env php
<?php
if ($argc != 4) {
  print "Usage: generic_php.php <iv> <data>\n\n";
  exit(1);
}

$key = $argv[1];
$iv = $argv[2];
$d = $argv[3];

$key = base64_decode(strtr($key, '-_', '+/'), true);
$iv = base64_decode(strtr($iv, '-_', '+/'), true);
$d = base64_decode(strtr($d, '-_', '+/'), true);

$td = mcrypt_module_open("rijndael-128", "", "cbc", "");
mcrypt_generic_init($td, $key, $iv);
$decrypted = mdecrypt_generic($td, $d);
mcrypt_generic_deinit($td);
mcrypt_module_close($td);

parse_str($decrypted, $data);

if ($data['t'] < time() - 10) {
  print  "*** Authentication timestamp too old ***\n";
}

print "User: " . $data['u'] . "\n";
print "Email: " . $data['e'] . "\n";
print "First: " . $data['f'] . "\n";
print "Last: " . $data['l'] . "\n";
print "\n";
?>