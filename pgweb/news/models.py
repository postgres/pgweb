from django.db import models
from datetime import date
from pgweb.core.models import Organisation
from pgweb.util.bases import PgModel

class NewsArticle(PgModel, models.Model):
	org = models.ForeignKey(Organisation, null=False, blank=False)
	approved = models.BooleanField(null=False, blank=False, default=False)
	date = models.DateField(null=False, blank=False, default=date.today)
	title = models.CharField(max_length=200, null=False, blank=False)
	content = models.TextField(null=False, blank=False)

	send_notification = True
	markdown_fields = ('content',)
	
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
