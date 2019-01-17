#
# Script to sync lists from archives server
#

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.conf import settings
import requests

class Command(BaseCommand):
    help = 'Synchronize mailinglists'

    def add_arguments(self, parser):
        parser.add_argument('--dryrun', action='store_true', help="Don't commit changes")

    def handle(self, *args, **options):
        if settings.ARCHIVES_SEARCH_PLAINTEXT:
            proto="http"
        else:
            proto="https"
        r = requests.get('{0}://{1}/listinfo/'.format(proto, settings.ARCHIVES_SEARCH_SERVER))
        j = r.json()
        allgroups = list(set([l['group'] for l in j]))
        with transaction.atomic():
            curs = connection.cursor()

            # Add any groups necessary
            curs.execute("INSERT INTO lists_mailinglistgroup (groupname, sortkey) SELECT n,50 FROM UNNEST(%s) n(n) WHERE NOT EXISTS (SELECT 1 FROM lists_mailinglistgroup WHERE groupname=n) RETURNING groupname", (allgroups,))
            for n, in curs.fetchall():
                print "Added group %s" % n

            # Add and update lists
            for l in j:
                curs.execute("SELECT id FROM lists_mailinglist WHERE listname=%s", (l['name'],))
                if curs.rowcount == 0:
                    curs.execute("INSERT INTO lists_mailinglist (listname, group_id, active, description, shortdesc) VALUES (%s, (SELECT id FROM lists_mailinglistgroup WHERE groupname=%s), %s, %s, %s)", (
                        l['name'], l['group'], l['active'], l['description'], l['shortdesc']))
                    print "Added list %s" % l['name']
                else:
                    curs.execute("UPDATE lists_mailinglist SET group_id=(SELECT id FROM lists_mailinglistgroup WHERE groupname=%s), active=%s, description=%s, shortdesc=%s WHERE listname=%s AND NOT (group_id=(SELECT id FROM lists_mailinglistgroup WHERE groupname=%s) AND active=%s AND description=%s AND shortdesc=%s) RETURNING listname", (
                        l['group'], l['active'], l['description'], l['shortdesc'],
                        l['name'],
                        l['group'], l['active'], l['description'], l['shortdesc'],
                    ))
                    for n, in curs.fetchall():
                        print "Updated list %s" % n

            # Delete any lists that shouldn't exist anymore (this is safe because we don't keep any data about them,
            # so they are trivial to add back)
            curs.execute("DELETE FROM lists_mailinglist WHERE NOT listname=ANY(%s) RETURNING listname", ([l['name'] for l in j],))
            for n, in curs.fetchall():
                print "Deleted list %s" % n
            # Delete listgroups
            curs.execute("DELETE FROM lists_mailinglistgroup WHERE NOT groupname=ANY(%s) RETURNING groupname", (allgroups,))
            for n, in curs.fetchall():
                print "Deleted group %s" % n

            if options['dryrun']:
                raise CommandError("Dry run, rolling back")
