#!/usr/bin/python3 -u
#
# auth_changetrack.py - tracks changes to users and distributes them
#

import sys
import select
import requests
import json
import base64
import hmac
import logging
import psycopg2
import psycopg2.extensions


def process_queue(conn):
    site_stoplist = []
    curs = conn.cursor()

    while True:
        # Fetch data for one site at a time, by just picking whatever happens to be the oldest one
        curs.execute("SELECT site_id, apiurl, cryptkey, push_ssh FROM (SELECT site_id FROM account_communityauthchangelog WHERE NOT site_id=ANY(%(stoplist)s) LIMIT 1) x INNER JOIN account_communityauthsite s ON s.id=x.site_id", {
            'stoplist': site_stoplist,
        })
        if not curs.rowcount:
            # Nothing in the queue, so we're done here.
            return

        siteid, url, cryptkey, include_ssh = curs.fetchone()

        # Get all data for this site (well, up to 100 users to not generate packages that are too big... We'll come back for the rest later if there are more.
        curs.execute(
            """SELECT cl.user_id, changedat, username, first_name, last_name, u.email, sshkey, array_agg(se.email) FILTER (WHERE se.confirmed AND se.email IS NOT NULL)
FROM account_communityauthchangelog cl
INNER JOIN auth_user u ON u.id=cl.user_id
LEFT JOIN account_secondaryemail se ON se.user_id=cl.user_id
LEFT JOIN core_userprofile up ON up.user_id=cl.user_id
WHERE cl.site_id=%(siteid)s
GROUP BY cl.user_id, cl.changedat, u.id, up.user_id
LIMIT 100""",
            {
                'siteid': siteid,
            }
        )
        rows = curs.fetchall()
        if not rows:
            # This shouldn't happen
            logging.error("Re-querying for updates returned no rows! Aborting.")
            return

        # Build the update structure
        def _get_userid_struct(row):
            yield 'username', row[2]
            yield 'firstname', row[3]
            yield 'lastname', row[4]
            yield 'email', row[5]
            yield 'secondaryemails', row[7] or []
            if include_ssh:
                yield 'sshkeys', row[6]

        pushstruct = {
            'type': 'update',
            'users': [dict(_get_userid_struct(row)) for row in rows],
        }
        pushjson = json.dumps(pushstruct)

        # We don't need to encrypt since it's over https, but we need to sign.
        h = hmac.digest(
            base64.b64decode(cryptkey),
            msg=bytes(pushjson, 'utf-8'),
            digest='sha512',
        )

        try:
            r = requests.post(url, data=pushjson, headers={
                'X-pgauth-sig': base64.b64encode(h),
            }, timeout=10)
        except Exception as e:
            logging.error("Exception pushing changes to {}: {}".format(url, e))
            site_stoplist.append(siteid)
            continue

        if r.status_code == 200:
            # Success! Whee!
            # This is a really silly way to do it, but meh.
            # Also psycopg2 really doesn't like mixing transaction modes, but here we go..
            conn.autocommit = False
            curs.executemany("DELETE FROM account_communityauthchangelog WHERE site_id=%(siteid)s AND user_id=%(userid)s AND changedat=%(changedat)s", [
                {
                    'siteid': siteid,
                    'userid': row[0],
                    'changedat': row[1],
                } for row in rows]
            )
            logging.info("Successfully pushed {} changes to {}".format(len(rows), url))
            conn.commit()
            conn.autocommit = True
            continue

        logging.error("Failed to push changes to {}: status {}, initial: {}".format(url, r.status_code, r.text[:100]))
        site_stoplist.append(siteid)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: auth_changetrack.py <dsn>")
        sys.exit(1)

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

    conn = psycopg2.connect(sys.argv[1])
    curs = conn.cursor()

    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_REPEATABLE_READ)
    conn.autocommit = True

    curs.execute("LISTEN communityauth_changetrack")

    while True:
        process_queue(conn)

        select.select([conn], [], [], 5 * 60)
        conn.poll()
        while conn.notifies:
            conn.notifies.pop()
        # Loop back up and process the full queue
