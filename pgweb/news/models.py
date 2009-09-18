from django.db import models
from django.contrib.auth.models import User
from datetime import date
from pgweb.util.bases import PgModel

class NewsArticle(PgModel, models.Model):
	submitter = models.ForeignKey(User, null=False, blank=False)
	approved = models.BooleanField(null=False, blank=False, default=False)
	date = models.DateField(null=False, blank=False, default=date.today)
	title = models.CharField(max_length=200, null=False, blank=False)
	content = models.TextField(null=False, blank=False)

	send_notification = True
	markdown_fields = ('content',)
	
	def __unicode__(self):
		return "%s: %s" % (self.date, self.title)
	
	class Meta:
		ordering = ('-date',)
