#!/usr/bin/env python
import sys
import os
from datetime import datetime

# Set up for accessing django
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '../../pgweb'))
import settings
setup_environ(settings)

from django.db import connection

from util.moderation import get_all_pending_moderations
from util.misc import send_template_mail

counts = [{'name': unicode(x['name']), 'count': len(x['entries'])} for x in get_all_pending_moderations()]
if len(counts):
	# Generate an email and send it off
	send_template_mail(settings.NOTIFICATION_FROM,
					   settings.NOTIFICATION_EMAIL,
					   "PostgreSQL moderation report: %s" % datetime.now(),
					   "core/moderation_report.txt",
					   {
			'items': counts,
			})

connection.close()
