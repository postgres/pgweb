#!/usr/bin/env python

#
# This script generates a crypto key that can be used for
# community authentication integration.
#

from Crypto import Random
import base64

if __name__ == "__main__":
    print "The next row contains a 32-byte (256-bit) symmetric crypto key."
    print "This key should be used to integrate a community auth site."
    print "Note that each site should have it's own key!!"
    print ""

    r = Random.new()
    key = r.read(32)
    print base64.b64encode(key)
    
