from django.db import models
from datetime import date
from pgweb.core.models import Organisation
from pgweb.util.bases import PgModel

class NewsArticle(PgModel, models.Model):
	org = models.ForeignKey(Organisation, null=False, blank=False, help_text="If no organisations are listed, please check the <a href=\"/account/orglist/\">organisation list</a> and contact the organisation manager or webmaster@postgresql.org if none are listed.")
	approved = models.BooleanField(null=False, blank=False, default=False)
	date = models.DateField(null=False, blank=False, default=date.today)
	title = models.CharField(max_length=200, null=False, blank=False)
	content = models.TextField(null=False, blank=False)

	send_notification = True
	markdown_fields = ('content',)

	def purge_urls(self):
		yield '/about/news/%s/' % self.pk
		yield '/about/newsarchive/'
		yield '/news.rss'
		# FIXME: when to expire the front page?
		yield '/$'
	
	def __unicode__(self):
		return "%s: %s" % (self.date, self.title)
	
	def verify_submitter(self, user):
		return (len(self.org.managers.filter(pk=user.pk)) == 1)

	def is_migrated(self):
		if self.org.pk == 0:
			return True
		return False

	class Meta:
		ordering = ('-date',)
