#!/usr/bin/env python

#
# This script generates a URL valid for a test authentication,
# so the full website integration isn't necessary.
#

import sys
from Crypto import Random
from Crypto.Cipher import AES
from urllib import quote_plus
import base64
import urllib
from optparse import OptionParser


if __name__ == "__main__":
	parser = OptionParser()
	parser.add_option("-k", "--key", dest="key")
	parser.add_option("-u", "--user", dest="user")
	parser.add_option("-f", "--first", dest="first")
	parser.add_option("-l", "--last", dest="last")
	parser.add_option("-e", "--email", dest="email")
	parser.add_option("-s", "--suburl", dest="suburl")

	(options, args) = parser.parse_args()

	if len(args) != 0:
		parser.print_usage()
		sys.exit(1)

	if not options.key:
		options.key = raw_input("Enter key (BASE64 encoded): ")
	if not options.user:
		options.user = raw_input("Enter username: ")
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
	if options.suburl:
		info['su'] = options.suburl

	s = urllib.urlencode(info)

	r = Random.new()
	iv = r.read(16)
	encryptor = AES.new(base64.b64decode(options.key), AES.MODE_CBC, iv)
	cipher = encryptor.encrypt(s + ' ' * (16-(len(s) % 16)))

	print "Paste the following after the receiving url:"
	print "?i=%s&d=%s" % (
		base64.b64encode(iv, "-_"),
		base64.b64encode(cipher, "-_"),
		)
