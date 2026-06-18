#!/usr/bin/env python3
#
# Script to run for news once per hour. Does:
#  * Post articles that were previously embargoed but the embargo has expired
#
#

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from datetime import datetime, date

from pgweb.util.moderation import ModerationState
from pgweb.news.models import NewsArticle, NewsPostingEmbargo
from pgweb.mailqueue.util import send_simple_mail


class Command(BaseCommand):
    help = 'News hourly'

    def handle(self, *args, **options):
        self.post_embargoed_news()

    @transaction.atomic
    def post_embargoed_news(self):
        # Fetch up to 2 article, to see if there is more than one in the queue
        if articles := list(NewsArticle.objects.filter(modstate=ModerationState.EMBARGOED).order_by('date')[:2]):
            # One or more embargoed articles. Do we have an active embargo?
            if not NewsPostingEmbargo.objects.filter(duration__contains=datetime.now()):
                # No embargo! So we post *one* news item at this point. If there is more than one, we will come back
                # and post it on the next iteration.
                a = articles[0]
                a.modstate = ModerationState.APPROVED
                a.date = date.today()
                a.send_notification = False  # We'll send our own notification
                a.save(update_fields=['modstate', 'date'])
                a.on_approval(None)

                if len(articles) > 1:
                    extra = "\nThere exists at least one more embargoed article.\nThis will be posted next hour, to spread them out.\n"
                else:
                    extra = ""

                # Send a notification to moderators only
                send_simple_mail(
                    settings.NOTIFICATION_FROM,
                    settings.NOTIFICATION_EMAIL,
                    "News article released from embargo",
                    "The news article with title '{}'\nhas been released from embargo and is now posted.\n{}".format(a.title, extra),
                )
