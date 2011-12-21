#!/usr/bin/perl
#
# This is just a generic function that handles the decryption and parsing steps as
# an example, it's not a complete authentication plugin (since that will be framework
# dependent)
#

use strict;
use warnings;

use 5.10.0;

use Crypt::CBC;
use MIME::Base64 qw(decode_base64url);
use URI::Escape qw(uri_unescape);
use Data::Dumper qw(Dumper);

sub encrypted_b64_to_hash {
    my ($iv, $key, $data) = map { decode_base64url($_) } @_;
                
    my $cipher = Crypt::CBC->new(
        -literal_key    => 1,
        -key            => $key,
        -iv             => $iv,
        -cipher         => 'Crypt::OpenSSL::AES',
        -header         => 'none',
    );
        
    return map { /^(.*?)=(.*)/ ? ( $1 => uri_unescape($2) ) : () } split /&/, $cipher->decrypt($data);
}
