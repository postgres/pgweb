from django.contrib.syndication.views import Feed
from django.template.defaultfilters import slugify

from .models import Event

from datetime import datetime, time


class EventFeed(Feed):
    title = description = "PostgreSQL events"
    link = "https://www.postgresql.org/"

    description_template = 'events/rss_description.html'
    title_template = 'events/rss_title.html'

    def items(self):
        return Event.objects.filter(approved=True)[:10]

    def item_link(self, obj):
        return "https://www.postgresql.org/about/event/{}-{}/".format(slugify(event.title), obj.id)

    def item_pubdate(self, obj):
        return datetime.combine(obj.startdate, time.min)
