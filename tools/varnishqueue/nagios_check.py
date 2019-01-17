#!/usr/bin/env python

import sys
import psycopg2
from datetime import timedelta

# Up to 5 minutes delay is ok
WARNING_THRESHOLD=timedelta(minutes=5)
# More than 15 minutes something is definitely wrong
CRITICAL_THRESHOLD=timedelta(minutes=15)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "Usage: nagios_check.py <dsn>"
        sys.exit(1)

    conn = psycopg2.connect(sys.argv[1])
    curs = conn.cursor()

    # Get the oldest entry that has not been completed, if any
    curs.execute("SELECT COALESCE(max(now()-added), '0') FROM varnishqueue.queue WHERE completed IS NULL")
    rows = curs.fetchall()
    conn.close()

    if len(rows) == 0:
        print "OK, queue is empty"
        sys.exit(0)

    age = rows[0][0]

    if age < WARNING_THRESHOLD:
        print "OK, queue age is %s" % age
        sys.exit(0)
    elif age < CRITICAL_THRESHOLD:
        print "WARNING, queue age is %s" % age
        sys.exit(1)
    else:
        print "CRITICAL, queue age is %s" % age
        sys.exit(2)
