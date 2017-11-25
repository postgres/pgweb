from django.db import models

class MailingListGroup(models.Model):
	groupname = models.CharField(max_length=64, null=False, blank=False)
	sortkey = models.IntegerField(null=False, default=10)

	purge_urls = ('/community/lists/', )

	@property
	def negid(self):
		return -self.id

	def __unicode__(self):
		return self.groupname

	class Meta:
		ordering = ('sortkey', )

class MailingList(models.Model):
	group = models.ForeignKey(MailingListGroup, null=False)
	listname = models.CharField(max_length=64, null=False, blank=False, unique=True)
	active = models.BooleanField(null=False, default=False)
	externallink = models.URLField(max_length=200, null=True, blank=True)
	description = models.TextField(null=False, blank=True)
	shortdesc = models.TextField(null=False, blank=True)

	purge_urls = ('/community/lists/', )

	@property
	def maybe_shortdesc(self):
		if self.shortdesc:
			return self.shortdesc
		return self.listname

	def __unicode__(self):
		return self.listname

	class Meta:
		ordering = ('listname', )
