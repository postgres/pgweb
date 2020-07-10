#!/usr/bin/env python3
#
# Script to send out a news email
# THIS IS FOR TESTING ONLY
# Normal emails are triggered automatically on moderation!
# Note that emails are queued up in the MailQueue model, to be sent asynchronously
# by the sender (or viewed locally).
#
#

from django.core.management.base import BaseCommand, CommandError

from pgweb.news.models import NewsArticle
from pgweb.news.util import send_news_email


def yesno(prompt):
    while True:
        r = input(prompt)
        if r.lower().startswith('y'):
            return True
        elif r.lower().startswith('n'):
            return False


class Command(BaseCommand):
    help = 'Test news email'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int, help='id of news article to post')

    def handle(self, *args, **options):
        try:
            news = NewsArticle.objects.get(pk=options['id'])
        except NewsArticle.DoesNotExist:
            raise CommandError("News article not found.")

        print("Title: {}".format(news.title))
        print("Moderation state: {}".format(news.modstate_string))
        if not yesno('Proceed to send mail for this article?'):
            raise CommandError("OK, aborting")

        send_news_email(news)
        print("Sent.")
