#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.log import log
from lib.archives import MultiListCrawler
from lib.threadwrapper import threadwrapper
from ConfigParser import ConfigParser
from optparse import OptionParser
import psycopg2
import sys
import time


def doit(opt):
    cp = ConfigParser()
    cp.read("search.ini")
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    conn = psycopg2.connect(cp.get("search", "db"))

    curs = conn.cursor()

    if opt.list:
        # Multiple lists can be specified with a comma separator (no spaces)
        curs.execute("SELECT id,name FROM lists WHERE name=ANY(%(names)s)", {
            'names': opt.list.split(','),
        })
    else:
        curs.execute("SELECT id,name FROM lists WHERE active ORDER BY id")

    listinfo = [(id, name) for id, name in curs.fetchall()]
    c = MultiListCrawler(listinfo, conn, opt.status_interval, opt.commit_interval)
    n = c.crawl(opt.full, opt.month)

    # Update total counts
    curs.execute("WITH t AS (SELECT list,count(*) AS c FROM messages GROUP BY list) UPDATE lists SET pagecount=t.c FROM t WHERE id=t.list")
    # Indicate when we crawled
    curs.execute("UPDATE lastcrawl SET lastcrawl=CURRENT_TIMESTAMP")
    conn.commit()

    log("Indexed %s messages" % n)
    time.sleep(1)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-l", "--list", dest='list', help="Crawl only this list")
    parser.add_option("-m", "--month", dest='month', help="Crawl only this month")
    parser.add_option("-f", "--full", dest='full', action="store_true", help="Make a full crawl")
    parser.add_option("-t", "--status-interval", dest='status_interval', help="Seconds between status updates")
    parser.add_option("-c", "--commit-interval", dest='commit_interval', help="Messages between each commit")

    (opt, args) = parser.parse_args()

    if opt.full and opt.month:
        print("Can't use both full and specific month!")
        sys.exit(1)

    # assign default values
    opt.status_interval = opt.status_interval and int(opt.status_interval) or 30
    opt.commit_interval = opt.commit_interval and int(opt.commit_interval) or 500

    threadwrapper(doit, opt)
