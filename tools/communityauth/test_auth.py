#!/usr/bin/env python3

#
# This script generates a URL valid for a test authentication,
# so the full website integration isn't necessary.
#

import sys
from Cryptodome import Random
from Cryptodome.Cipher import AES
import base64
import time
import urllib.parse
from optparse import OptionParser


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-k", "--key", dest="key")
    parser.add_option("-u", "--user", dest="user")
    parser.add_option("-f", "--first", dest="first")
    parser.add_option("-l", "--last", dest="last")
    parser.add_option("-e", "--email", dest="email")

    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.print_usage()
        sys.exit(1)

    if not options.key:
        options.key = input("Enter key (BASE64 encoded): ")
    if not options.user:
        options.user = input("Enter username: ")
    if not options.first:
        options.first = "FirstName"
    if not options.last:
        options.last = "LastName"
    if not options.email:
        options.email = "test@example.com"

    # This is basically a rip of the view in accounts/views.py
    info = {
        'u': options.user,
        'f': options.first,
        'l': options.last,
        'e': options.email,
    }

    # Turn this into an URL. Make sure the timestamp is always first, that makes
    # the first block more random..
    # Since this is a fake authentication, put it 5 minutes into the future to
    # give more time to copy/paste it.
    s = "t=%s&%s" % (int(time.time() + 300), urllib.parse.urlencode(info))

    r = Random.new()
    nonce = r.read(16)
    encryptor = AES.new(
        base64.b64decode(options.key),
        AES.MODE_SIV,
        nonce=nonce,
    )
    cipher, tag = encryptor.encrypt_and_digest(s.encode('ascii'))

    redirparams = {
        'd': base64.urlsafe_b64encode(cipher).decode('ascii'),
        'n': base64.urlsafe_b64encode(nonce).decode('ascii'),
        't': base64.urlsafe_b64encode(tag).decode('ascii'),
    }

    print("Paste the following after the receiving url:")
    print("?" + urllib.parse.urlencode(redirparams))
