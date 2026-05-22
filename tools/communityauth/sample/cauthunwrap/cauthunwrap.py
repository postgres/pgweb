#!/usr/bin/env python3
#
# postgresql.org community authentication unwrapper
#
# This file should be mapped to an auth receive URL and will read the data
# received and return it as json as a standard http response. If the response
# code is 200 it means the authentication was successful, and it's then up to
# the caller to create a session. Any other response code (typically 400 or 500)
# means authentication was *not* successful.
#
# Intended to be called as a nginx subrequest as part of an authentication setup.
# Note that some sort of session management is normally needed to be built on the
# calling side, to avoid making a new authentication redirect on every single call.
#

import base64
import json
import os
import sys
import configparser
import http.client
import time
from urllib.parse import parse_qs
from Cryptodome.Cipher import AES

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(__file__, '../cauthunwrap.ini')))


def application(environ, start_response):
    def _respond(code, txt, content_type='text/plain'):
        start_response(
            '{} {}'.format(code, http.client.responses.get(code, 'Unknown')),
            [('Content-type', content_type)],
        )
        return [txt.encode()]

    try:
        if environ['REQUEST_METHOD'] != 'GET':
            return _respond(400, "Only GET allowed")

        q = parse_qs(environ.get('QUERY_STRING', ''), strict_parsing=True)
        if 'n' not in q:
            return _respond(400, 'Missing nonce')
        if 'd' not in q:
            return _respond(400, 'Missing data')
        if 't' not in q:
            return _respond(400, 'Missing tag')

        try:
            decryptor = AES.new(
                base64.b64decode(config.get('pgauth', 'key')),
                AES.MODE_SIV,
                nonce=base64.urlsafe_b64decode(q['n'][0]),
            )
            s = decryptor.decrypt_and_verify(
                base64.urlsafe_b64decode(q['d'][0]),
                base64.urlsafe_b64decode(q['t'][0]),
            ).rstrip(b' ').decode('utf8')
        except UnicodeDecodeError:
            return _respond(400, "Badly encoded data found")
        except Exception as e:
            print("Decrypt error: {}".format(e))
            return _respond(400, "Could not decrypt data")

        try:
            data = parse_qs(s, strict_parsing=True)
        except ValueError:
            return _respond(400, "Invalid encrypted data received.")

        if (int(data['t'][0]) < time.time() - 10):
            return _respond(400, "Authentication token too old.")

        data = {k: v[0] for k, v in data.items() if k != 't'}

        return _respond(200, json.dumps(data), 'application/json')
    except Exception as e:
        print("Error receiving authentication: {}".format(e), file=sys.stderr)
        return _respond('500', 'An internal error occurred')
