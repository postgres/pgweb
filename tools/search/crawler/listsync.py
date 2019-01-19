#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lib.log import log
from ConfigParser import ConfigParser
import psycopg2
import urllib
import simplejson as json

if __name__ == "__main__":
    cp = ConfigParser()
    cp.read("search.ini")
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    conn = psycopg2.connect(cp.get("search", "db"))
    curs = conn.cursor()

    u = urllib.urlopen("http://%s/community/lists/listinfo/" % cp.get("search", "web"))
    obj = json.load(u)
    u.close()

    # We don't care about the groups here, just the lists!
    curs.execute("SELECT id, name, grp, active FROM lists")
    lists = curs.fetchall()
    for id, name, groupid, active in lists:
        thislist = [x for x in obj['lists'] if x['id'] == id]
        if len(thislist) == 0:
            log("List %s should be removed, do that manually!" % name)
        else:
            # Compare contents of list
            l = thislist[0]
            if l['name'] != name:
                log("Renaming list %s -> %s" % (name, l['name']))
                curs.execute("UPDATE lists SET name=%(name)s WHERE id=%(id)s", l)

            if thislist[0]['active'] != active:
                log("Changing active flag for %s to %s" % (l['name'], l['active']))
                curs.execute("UPDATE lists SET active=%(active)s WHERE id=%(id)s", l)
            if thislist[0]['groupid'] != groupid:
                log("Changing group for %s to %s" % (l['name'], l['groupid']))
                curs.execute("UPDATE lists SET grp=%(groupid)s WHERE id=%(id)s", l)

    for l in obj['lists']:
        thislist = [x for x in lists if x[0] == l['id']]
        if len(thislist) == 0:
            log("Adding list %s" % l['name'])
            curs.execute("INSERT INTO lists (id, name, grp, active, pagecount) VALUES (%(id)s, %(name)s, %(groupid)s, %(active)s, 0)",
                         l)

    conn.commit()
