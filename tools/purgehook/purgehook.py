#!/usr/bin/env python
#
# This hook script is run by gitdeployer when the code is
# deployed to a server. figure out which templates have been
# modified and queue automatic purges for them.
# Gitdeployer will pass a list of all modified files on
# stdin.

import sys
import os
import hashlib
from ConfigParser import ConfigParser
import psycopg2

# Templates that we don't want to ban automatically
BANNED_TEMPLATES=(
	'base/base.html',
)

if __name__ == "__main__":
	config = ConfigParser()
	config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'purgehook.ini'))
	conn = psycopg2.connect(config.get('db', 'dsn'))
	curs = conn.cursor()

	for l in sys.stdin:
		tmpl = l[len('templates/'):].strip()
		if not tmpl in BANNED_TEMPLATES:
			curs.execute("SELECT varnish_purge_xkey(%(key)s)", {
				'key': 'pgwt_{0}'.format(hashlib.md5(tmpl).hexdigest()),
			})
	conn.commit()
	conn.close()
