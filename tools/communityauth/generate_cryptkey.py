#!/usr/bin/env python3

#
# This script generates a crypto key that can be used for
# community authentication integration.
#

from Cryptodome import Random
import base64
import sys


def usage():
    print("Usage: generate_cryptkey.py <version>")
    print("")
    print("Version must be 3 or 4, representing the version of community authentication encryption to use")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
    if sys.argv[1] not in ("3", "4"):
        usage()

    version = int(sys.argv[1])
    keylen = 64 if version == 3 else 32

    print("The next row contains a {}-byte ({}-bit) symmetric crypto key.".format(keylen, keylen * 8))
    print("This key should be used to integrate a community auth site.")
    print("Note that each site should have it's own key!!")
    print("")

    r = Random.new()
    key = r.read(keylen)
    print(base64.b64encode(key).decode('ascii'))
