from django.contrib.syndication.feeds import Feed

from models import PwnPost

from datetime import datetime, time

class PwnFeed(Feed):
	title = description = "PostgreSQL Weekly News"
	link = "http://www.postgresql.org/community/weeklynews/"

	description_template = 'pwn/rss_description.html'
	title_template = 'pwn/rss_title.html'

	def items(self):
		return PwnPost.objects.all()[:5]

	def item_link(self, obj):
		return "http://www.postgresql.org/community/weeklynews/pwn%s/" % obj.linkdate

	def item_pubdate(self, obj):
		return datetime.combine(obj.date,time.min)

