#!/usr/bin/env python

import feedparser
import psycopg2
import socket


# Set timeout for loading RSS feeds
socket.setdefaulttimeout(20)


db = psycopg2.connect('host=/tmp dbname=pgweb')
curs = db.cursor()
curs.execute("SELECT id,internalname,url FROM core_importedrssfeed")
for id,internalname,url in curs.fetchall():
	try:
		feed = feedparser.parse(url)
		
		if not hasattr(feed, 'status'):
			# bozo_excpetion can seemingly be set when there is no error as well,
			# so make sure we only check if we didn't get a status.
			if hasattr(feed,'bozo_exception'):
				raise Exception('Feed load error %s' % feed.bozo_exception)
			raise Exception('Feed load error with no exception!')
		if feed.status != 200:
			raise Exception('Feed returned status %s' % feed.status)
		for entry in feed.entries:
			curs.execute("""INSERT INTO core_importedrssitem (feed_id, title, url, posttime)
SELECT %(feed)s, %(title)s, %(url)s, %(posttime)s
WHERE NOT EXISTS (SELECT * FROM core_importedrssitem c2 WHERE c2.feed_id=%(feed)s AND c2.url=%(url)s)""", {
				'feed': id,
				'title': entry.title,
				'url': entry.link,
				'posttime': entry.date,
			})
	except Exception, e:
		print "Failed to load %s: %s" % (internalname, e)

db.commit()

