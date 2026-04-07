#!/usr/bin/env python3
#
# Script to post previously unposted news to social media providers
#
#

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.template.defaultfilters import slugify
from django.conf import settings

from datetime import datetime, timedelta
import time

from pgweb.util.moderation import ModerationState
from pgweb.news.models import NewsArticle, PinnedNewsArticle
from pgweb.util.socialposter import get_all_providers


allproviders, allprovidernames = get_all_providers(settings)


class Command(BaseCommand):
    help = 'Post to social media'

    def handle(self, *args, **options):
        if not allprovidernames:
            # If we have no providers, there is no posting
            return

        curs = connection.cursor()
        curs.execute("SELECT pg_try_advisory_lock(62387372)")
        if not curs.fetchall()[0][0]:
            raise CommandError("Failed to get advisory lock, existing social_post process stuck?")

        articles = list(NewsArticle.objects.filter(modstate=ModerationState.APPROVED, date__gt=datetime.now() - timedelta(days=7)).exclude(postedto__has_keys=allprovidernames).order_by('date'))
        if not len(articles):
            return

        for i, a in enumerate(articles):
            if i != 0:
                # Don't post more often than once / 30 seconds, to not trigger flooding.
                time.sleep(30)

            statusstr = "News: {0}\n\n{1}/about/news/{2}-{3}/\n\n#postgresql".format(a.title[:140 - 40], settings.SITE_ROOT, slugify(a.title), a.id)

            for p in allproviders:
                if p.name not in a.postedto:
                    postid = p.post(statusstr)
                    if postid is not None:
                        a.postedto[p.name] = postid
                        a.save(update_fields=['postedto'])

        # Pin or unpin any articles as needed
        pna = PinnedNewsArticle.objects.select_related('pinnedarticle').only('pinnedarticle', 'pinnedtoproviders', 'pinnedarticle__postedto').all()[0]
        for p in allproviders:
            if pna.pinnedtoproviders.get(p.name, None) != pna.pinnedarticle.postedto.get(p.name, None):
                if p.set_pin(pna.pinnedarticle.postedto.get(p.name, None)):
                    pna.pinnedtoproviders[p.name] = pna.pinnedarticle.postedto.get(p.name, None)
                    pna.save(update_fields=['pinnedtoproviders'])
