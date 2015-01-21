#!/usr/bin/env python
#
# Script to generally cleanup old records in the database.
#
# Currently cleans up:
#
#  * Expired email change tokens
#
#

import sys
import os
from datetime import datetime, timedelta

# Set up to run in django environment
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '../../pgweb'))
import settings
setup_environ(settings)

from django.db import connection, transaction

from account.models import EmailChangeToken

if __name__ == "__main__":
	# Grab advisory lock, if available. Lock id is just a random number
	# since we only need to interlock against ourselves. The lock is
	# automatically released when we're done.
	curs = connection.cursor()
	curs.execute("SELECT pg_try_advisory_lock(2896719)")
	if not curs.fetchall()[0][0]:
		print "Failed to get advisory lock, existing cleanup_old_records process stuck?"
		sys.exit(1)

	# Clean up old email change tokens
	with transaction.commit_on_success():
		EmailChangeToken.objects.filter(sentat__lt=datetime.now()-timedelta(hours=24)).delete()

	# Proper close to avoid logging of disconnects
	connection.close()
