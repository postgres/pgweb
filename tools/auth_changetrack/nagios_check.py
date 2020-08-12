#!/usr/bin/env python3

import sys
import psycopg2
from datetime import timedelta

# Up to 5 minutes delay is ok
WARNING_THRESHOLD = timedelta(minutes=5)
# More than 15 minutes something is definitely wrong
CRITICAL_THRESHOLD = timedelta(minutes=15)


def check_queue(curs):
    # Get the oldest entry that has not been completed, if any
    curs.execute("SELECT COALESCE(now()-changedat) FROM account_communityauthchangelog")
    rows = curs.fetchall()

    if len(rows) == 0:
        return "queue is empty"
        sys.exit(0)

    age = rows[0][0]

    if age < WARNING_THRESHOLD:
        return "queue age is %s" % age
    elif age < CRITICAL_THRESHOLD:
        print("WARNING, queue age is %s" % age)
        sys.exit(1)
    else:
        print("CRITICAL, queue age is %s" % age)
        sys.exit(2)


def check_mail(curs):
    curs.execute("SELECT count(*) FROM (SELECT 1 FROM all_user_email_addresses GROUP BY email HAVING count(*) > 1) x")
    num, = curs.fetchone()
    if num > 0:
        print("CRITICAL, {} email addresses have duplicate entries!".format(num))
        sys.exit(2)
    return ""


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: nagios_check.py <dsn>")
        sys.exit(1)

    conn = psycopg2.connect(sys.argv[1])
    curs = conn.cursor()

    status = []
    status.append(check_queue(curs))
    status.append(check_mail(curs))

    print("OK: {}".format('; '.join([s for s in status if s])))
