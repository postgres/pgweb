from django.db import models

from pgweb.core.models import Country

class SponsorType(models.Model):
	typename = models.CharField(max_length=32, null=False, blank=False)
	description = models.TextField(null=False, blank=False)
	sortkey = models.IntegerField(null=False, default=10)
	# sortkey==0 --> do not show in list

	purge_urls = ('/about/servers/', '/about/sponsors/', )

	def __unicode__(self):
		return self.typename
	
	class Meta:
		ordering = ('sortkey', )
		
class Sponsor(models.Model):
	sponsortype = models.ForeignKey(SponsorType, null=False)
	name = models.CharField(max_length=128, null=False, blank=False)
	url = models.URLField(null=False, blank=False)
	logoname = models.CharField(max_length=64, null=False, blank=False)
	country = models.ForeignKey(Country, null=False)

	purge_urls = ('/about/sponsors/', '/about/servers/', )

	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('name', )

class Server(models.Model):
	name = models.CharField(max_length=32, null=False, blank=False)
	sponsors = models.ManyToManyField(Sponsor)
	dedicated = models.BooleanField(null=False, default=True)
	performance = models.CharField(max_length=128, null=False, blank=False)
	os = models.CharField(max_length=32, null=False, blank=False)
	location = models.CharField(max_length=128, null=False, blank=False)
	usage = models.TextField(null=False, blank=False)
	
	purge_urls = ('/about/servers/', )

	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('name', )

