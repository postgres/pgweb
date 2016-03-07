from django.db import models
from django.contrib.auth.models import User

class ContributorType(models.Model):
	typename = models.CharField(max_length=32, null=False, blank=False)
	sortorder = models.IntegerField(null=False, default=100)
	extrainfo = models.TextField(null=True, blank=True)
	detailed = models.BooleanField(null=False, default=True)

	purge_urls = ('/community/contributors/', )

	def __unicode__(self):
		return self.typename
	
	class Meta:
		ordering = ('sortorder',)

class Contributor(models.Model):
	ctype = models.ForeignKey(ContributorType)
	lastname = models.CharField(max_length=100, null=False, blank=False)
	firstname = models.CharField(max_length=100, null=False, blank=False)
	email = models.EmailField(null=False, blank=False)
	company = models.CharField(max_length=100, null=True, blank=True)
	companyurl = models.URLField(max_length=100, null=True, blank=True, verbose_name='Company URL')
	location = models.CharField(max_length=100, null=True, blank=True)
	contribution = models.TextField(null=True, blank=True)
	user = models.ForeignKey(User, null=True, blank=True)

	send_notification=True
	purge_urls = ('/community/contributors/', )

	def __unicode__(self):
		return "%s %s" % (self.firstname, self.lastname)
	
	class Meta:
		ordering = ('lastname', 'firstname',)
