from django.db import models
from datetime import date
from pgweb.core.models import Organisation

class NewsTag(models.Model):
	urlname = models.CharField(max_length=20, null=False, blank=False, unique=True)
	name = models.CharField(max_length=32, null=False, blank=False)
	description = models.CharField(max_length=200, null=False, blank=False)

	def __unicode__(self):
		return self.name

class NewsArticle(models.Model):
	org = models.ForeignKey(Organisation, null=False, blank=False, verbose_name="Organisation", help_text="If no organisations are listed, please check the <a href=\"/account/orglist/\">organisation list</a> and contact the organisation manager or webmaster@postgresql.org if none are listed.")
	approved = models.BooleanField(null=False, blank=False, default=False)
	date = models.DateField(null=False, blank=False, default=date.today)
	title = models.CharField(max_length=200, null=False, blank=False)
	content = models.TextField(null=False, blank=False)
	tweeted = models.BooleanField(null=False, blank=False, default=False)
	tags = models.ManyToManyField(NewsTag, blank=False, help_text="Hover mouse over tags to view full description")

	send_notification = True
	send_m2m_notification = True
	markdown_fields = ('content',)

	def purge_urls(self):
		yield '/about/news/%s/' % self.pk
		yield '/about/newsarchive/'
		yield '/news.rss'
		yield '/news/.*.rss'
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

	@property
	def displaydate(self):
		return self.date.strftime("%Y-%m-%d")

	class Meta:
		ordering = ('-date',)
