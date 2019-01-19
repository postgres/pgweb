#!/usr/bin/env python3
#
# Script to send daily moderation report to the NOTIFICATION_EMAIL address
# (the moderators list)
#
#

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from datetime import datetime

from pgweb.util.moderation import get_all_pending_moderations
from pgweb.util.misc import send_template_mail


class Command(BaseCommand):
    help = 'Send moderation report'

    def handle(self, *args, **options):
        with transaction.atomic():
            counts = [{'name': str(x['name']), 'count': len(x['entries'])} for x in get_all_pending_moderations()]
            if len(counts):
                # Generate an email and send it off
                send_template_mail(settings.NOTIFICATION_FROM,
                                   settings.NOTIFICATION_EMAIL,
                                   "PostgreSQL moderation report: %s" % datetime.now(),
                                   "core/moderation_report.txt",
                                   {
                                       'items': counts,
                                   })
