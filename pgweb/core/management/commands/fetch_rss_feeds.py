#!/usr/bin/env python3
#
# Script to fetch content from RSS feeds into the db for publishing.
#
#

from django.core.management.base import BaseCommand
from django.db import transaction

import socket
import feedparser
from datetime import datetime

from pgweb.core.models import ImportedRSSFeed, ImportedRSSItem


class Command(BaseCommand):
    help = 'Fetch RSS feeds'

    def handle(self, *args, **options):
        socket.setdefaulttimeout(20)

        with transaction.atomic():
            for importfeed in ImportedRSSFeed.objects.all():
                try:
                    feed = feedparser.parse(importfeed.url)

                    if not hasattr(feed, 'status'):
                        # bozo_excpetion can seemingly be set when there is no error as well,
                        # so make sure we only check if we didn't get a status.
                        if hasattr(feed, 'bozo_exception'):
                            raise Exception('Feed load error %s' % feed.bozo_exception)
                        raise Exception('Feed load error with no exception!')
                    if feed.status != 200:
                        raise Exception('Feed returned status %s' % feed.status)

                    fetchedsomething = False
                    for entry in feed.entries:
                        try:
                            item = ImportedRSSItem.objects.get(feed=importfeed, url=entry.link)
                        except ImportedRSSItem.DoesNotExist:
                            item = ImportedRSSItem(
                                feed=importfeed,
                                title=entry.title[:100],
                                url=entry.link,
                                posttime=datetime(*(entry.published_parsed[0:6])),
                            )
                            item.save()
                            fetchedsomething = True

                    if fetchedsomething:
                            importfeed.purge_related()
                except Exception as e:
                    print("Failed to load %s: %s" % (importfeed, e))
