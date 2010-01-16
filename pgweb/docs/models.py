from django.db import models
from django.contrib.auth.models import User
from pgweb.util.bases import PgModel

from datetime import datetime

class DocPage(models.Model):
	id = models.AutoField(null=False, primary_key=True)
	file = models.CharField(max_length=64, null=False, blank=False)
	version = models.DecimalField(max_digits=3, decimal_places=1, null=False)
	title = models.CharField(max_length=256, null=True, blank=True)
	content = models.TextField(null=True, blank=True)

	class Meta:
		db_table = 'docs'

class DocComment(PgModel, models.Model):
	version = models.DecimalField(max_digits=3, decimal_places=1, null=False)
	file = models.CharField(max_length=64, null=False, blank=False)
	comment = models.TextField(null=False, blank=False)
	posted_at = models.DateTimeField(null=False, blank=False, default=datetime.now())
	submitter = models.ForeignKey(User, null=False)
	approved = models.BooleanField(blank=False, default=False)

	send_notification = True

	class Meta:
		ordering = ('-posted_at',)

	@property
	def poster(self):
		if self.submitter_id > 0:
			print self.submitter
			return "%s %s" % (self.submitter.first_name, self.submitter.last_name)
		else:
			return ''
