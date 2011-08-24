from django.db import models
from django.contrib.auth.models import User

from pgweb.core.models import Organisation
from pgweb.util.bases import PgModel

class ProfessionalService(PgModel, models.Model):
	submitter = models.ForeignKey(User, null=False, blank=False)
	approved = models.BooleanField(null=False, blank=False, default=False)

	organisation = models.ForeignKey(Organisation, null=False, blank=False)
	description = models.TextField(null=False,blank=False)
	employees = models.CharField(max_length=32, null=True, blank=True)
	locations = models.CharField(max_length=128, null=True, blank=True)
	region_africa = models.BooleanField(null=False, default=False, verbose_name="Africa")
	region_asia = models.BooleanField(null=False, default=False, verbose_name="Asia")
	region_europe = models.BooleanField(null=False, default=False, verbose_name="Europe")
	region_northamerica = models.BooleanField(null=False, default=False, verbose_name="North America")
	region_oceania = models.BooleanField(null=False, default=False, verbose_name="Oceania")
	region_southamerica = models.BooleanField(null=False, default=False, verbose_name="South America")
	hours = models.CharField(max_length=128, null=True, blank=True)
	languages = models.CharField(max_length=128, null=True, blank=True)
	customerexample = models.TextField(blank=True, null=True, verbose_name="Customer Example")
	experience = models.TextField(blank=True, null=True)
	contact = models.TextField(null=True, blank=True)
	url = models.URLField(max_length=128, null=True, blank=True, verbose_name="URL")
	provides_support = models.BooleanField(null=False, default=False)
	provides_hosting = models.BooleanField(null=False, default=False)
	interfaces = models.CharField(max_length=512, null=True, blank=True, verbose_name="Interfaces (for hosting)")
	
	purge_urls = ('support/professional_', )
	
	send_notification = True
	
	def __unicode__(self):
		return self.organisation.name
	
	class Meta:
		ordering = ('organisation__name',)

