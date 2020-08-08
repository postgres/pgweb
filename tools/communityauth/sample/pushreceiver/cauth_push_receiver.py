#!/usr/bin/env python3
#
# postgresql.org community authentication push updates receiver
#
# This simple wsgi application is intended to run on systems that otherwise
# run a completely different codebase with just a simple authentication
# plugin, in order to receive push updates and materialize those into the
# database.
#
# It should be mapped to receive only the POST requests specifically for
# the community authentication API, and will act as that regardless of
# which URI it actually receives.
#

import os
import sys
import configparser
import json
import base64
import importlib
import hmac

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(__file__, '../cauth_push_receiver.ini')))


# Get the class ReceiverPlugin in the defined plugin
pluginclass = getattr(
    importlib.import_module('plugins.{}'.format(config.get('receiver', 'plugin'))),
    'ReceiverPlugin',
)


def application(environ, start_response):
    try:
        if environ['REQUEST_METHOD'] != 'POST':
            raise Exception("Only POST allowed")
        if 'HTTP_X_PGAUTH_SIG' not in environ:
            raise Exception("Required authentication header missing")

        try:
            sig = base64.b64decode(environ['HTTP_X_PGAUTH_SIG'])
        except Exception:
            raise Exception("Invalid signature header!")

        body = environ['wsgi.input'].read()

        try:
            h = hmac.digest(
                base64.b64decode(config.get('receiver', 'key')),
                msg=body,
                digest='sha512',
            )
        except Exception:
            raise Exception("Could not calculate hmac!")

        if not hmac.compare_digest(h, sig):
            raise Exception("Invalid signature!")

        try:
            pushstruct = json.loads(body)
        except Exception:
            raise Exception("Invalid json payload!")

        if pushstruct.get('type', None) == 'update':
            with pluginclass(config) as p:
                for u in pushstruct.get('users', []):
                    p.push_user(u)

        start_response('200 OK', [
            ('Content-type', 'text/plain'),
        ])
        return [
            "OK",
        ]
    except Exception as e:
        print("Error receiving cauth call: {}".format(e), file=sys.stderr)

        start_response('500 Internal Server Error', [
            ('Content-type', 'text/plain'),
        ])

        return [
            "An internal server error occurred.\n",
        ]
