from django.db import models

from pgweb.util.bases import PgModel

from datetime import date

class PwnPost(PgModel, models.Model):
	date = models.DateField(null=False, blank=False, default=date.today, unique=True)
	intro  = models.TextField(null=False, blank=False)
	content = models.TextField(null=False, blank=False)

	markdown_fields = ('intro', 'content',)

	def purge_urls(self):
		yield 'community/weeklynews/$'
		yield 'community/weeklynews/pwn%s/' % self.linkdate()
		yield 'weeklynews.rss'

	def __unicode__(self):
		return "PostgreSQL Weekly News %s" % self.date

	@property
	def linkdate(self):
		return self.date.strftime("%Y%m%d")

	@property
	def nicedate(self):
		return self.date.strftime("%B %d, %Y")

	class Meta:
		ordering = ('-date',)
