from django.contrib.syndication.feeds import Feed

from models import Version

from datetime import datetime, time

class VersionFeed(Feed):
	title = "PostgreSQL latest versions"
	link = "http://www.postgresql.org/"
	description = "PostgreSQL latest versions"

	description_template = 'core/version_rss_description.html'
	title_template = 'core/version_rss_title.html'

	def items(self):
		return Version.objects.filter(tree__gt=0)

	def item_link(self, obj):
		return "http://www.postgresql.org/docs/%s/static/%s" % (obj.tree, obj.relnotes)

	def item_pubdate(self, obj):
		return datetime.combine(obj.reldate,time.min)

