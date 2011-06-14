from django.db import models

from pgweb.util.bases import PgModel

class MailingListGroup(PgModel, models.Model):
	groupname = models.CharField(max_length=64, null=False, blank=False)
	sortkey = models.IntegerField(null=False, default=10)

	purge_urls = ('community/lists/', )

	def __unicode__(self):
		return self.groupname
	
	class Meta:
		ordering = ('sortkey', )

class MailingList(PgModel, models.Model):
	group = models.ForeignKey(MailingListGroup, null=False)
	listname = models.CharField(max_length=64, null=False, blank=False)
	active = models.BooleanField(null=False, default=False)
	externallink = models.URLField(max_length=200, null=True, blank=True)
	description = models.TextField(null=False, blank=True)
	shortdesc = models.TextField(null=False, blank=True)

	purge_urls = ('community/lists/', )

	@property
	def maybe_shortdesc(self):
		if self.shortdesc:
			return self.shortdesc
		return self.listname

	def __unicode__(self):
		return self.listname
	
	class Meta:
		ordering = ('listname', )
