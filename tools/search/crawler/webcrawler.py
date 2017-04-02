#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.log import log
from lib.genericsite import GenericSiteCrawler
from lib.sitemapsite import SitemapSiteCrawler
from lib.threadwrapper import threadwrapper

from ConfigParser import ConfigParser
import psycopg2
import time

def doit():
	psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
	conn = psycopg2.connect(cp.get("search","db"))

	curs = conn.cursor()

	# Start by indexing the main website
	log("Starting indexing of main website")
	SitemapSiteCrawler("www.postgresql.org", conn, 1, cp.get("search", "frontendip"), True).crawl()
	conn.commit()

	# Skip id=1, which is the main site..
	curs.execute("SELECT id, hostname, https FROM sites WHERE id>1")
	for siteid, hostname, https in curs.fetchall():
		log("Starting indexing of %s" % hostname)
		GenericSiteCrawler(hostname, conn, siteid, https).crawl()
		conn.commit()

	curs.execute("WITH t AS (SELECT site,count(*) AS c FROM webpages GROUP BY site) UPDATE sites SET pagecount=t.c FROM t WHERE id=t.site")
	conn.commit()

	time.sleep(1)


if __name__=="__main__":
	cp = ConfigParser()
	cp.read("search.ini")

	threadwrapper(doit)
