#!/usr/bin/env python3
#
# Script to generally cleanup old records in the database.
#
# Currently cleans up:
#
#  * Expired email change tokens
#
#

import sys

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from datetime import datetime, timedelta

from pgweb.account.models import SecondaryEmail
from pgweb.core.models import OrganisationEmail


class Command(BaseCommand):
    help = 'Cleanup old records'

    def handle(self, *args, **options):
        # Grab advisory lock, if available. Lock id is just a random number
        # since we only need to interlock against ourselves. The lock is
        # automatically released when we're done.
        curs = connection.cursor()
        curs.execute("SELECT pg_try_advisory_lock(2896719)")
        if not curs.fetchall()[0][0]:
            print("Failed to get advisory lock, existing cleanup_old_records process stuck?")
            sys.exit(1)

        # Clean up old email change tokens
        with transaction.atomic():
            SecondaryEmail.objects.filter(confirmed=False, sentat__lt=datetime.now() - timedelta(hours=24)).delete()
            OrganisationEmail.objects.filter(confirmed=False, added__lt=datetime.now() - timedelta(hours=72)).delete()
