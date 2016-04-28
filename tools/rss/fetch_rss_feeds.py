#!/usr/bin/env python

import feedparser
import socket
import sys
import os
from datetime import datetime

# Set up for accessing django
from django.core.management import setup_environ
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '../../pgweb'))
import settings
setup_environ(settings)

from pgweb.core.models import ImportedRSSFeed, ImportedRSSItem
from django.db import transaction, connection

# Set timeout for loading RSS feeds
socket.setdefaulttimeout(20)

transaction.enter_transaction_management()
transaction.managed()
for importfeed in ImportedRSSFeed.objects.all():
	try:
		feed = feedparser.parse(importfeed.url)
		
		if not hasattr(feed, 'status'):
			# bozo_excpetion can seemingly be set when there is no error as well,
			# so make sure we only check if we didn't get a status.
			if hasattr(feed,'bozo_exception'):
				raise Exception('Feed load error %s' % feed.bozo_exception)
			raise Exception('Feed load error with no exception!')
		if feed.status != 200:
			raise Exception('Feed returned status %s' % feed.status)
		fetchedsomething = False
		for entry in feed.entries:
			try:
				item = ImportedRSSItem.objects.get(feed=importfeed, url=entry.link)
			except ImportedRSSItem.DoesNotExist:
				item = ImportedRSSItem(feed=importfeed,
									   title=entry.title[:100],
									   url=entry.link,
									   posttime=datetime(*(entry.published_parsed[0:6])),
									   )
				item.save()
				fetchedsomething = True
		if fetchedsomething:
			importfeed.purge_related()
		transaction.commit()
	except Exception, e:
		print "Failed to load %s: %s" % (importfeed, e)

connection.close()
