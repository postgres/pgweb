from django.db import models
from django.contrib.auth.models import User

from pgweb.util.bases import PgModel

class ProfessionalService(models.Model):
	submitter = models.ForeignKey(User, null=False, blank=False)
	approved = models.BooleanField(null=False, blank=False, default=False)

	name = models.CharField(max_length=100, null=False, blank=False)
	description = models.TextField(null=False,blank=False)
	employees = models.CharField(max_length=32, null=True, blank=True)
	locations = models.CharField(max_length=128, null=True, blank=True)
	region_africa = models.BooleanField(null=False, default=False)
	region_asia = models.BooleanField(null=False, default=False)
	region_europe = models.BooleanField(null=False, default=False)
	region_northamerica = models.BooleanField(null=False, default=False)
	region_oceania = models.BooleanField(null=False, default=False)
	region_southamerica = models.BooleanField(null=False, default=False)
	hours = models.CharField(max_length=128, null=True, blank=True)
	languages = models.CharField(max_length=128, null=True, blank=True)
	customerexample = models.TextField(blank=True, null=True)
	experience = models.TextField(blank=True, null=True)
	contact = models.CharField(max_length=128, null=True, blank=True)
	url = models.URLField(max_length=128, null=True, blank=True)
	provides_support = models.BooleanField(null=False, default=False)
	provides_hosting = models.BooleanField(null=False, default=False)
	interfaces = models.CharField(max_length=128, null=True, blank=True)
	
	
	send_notification = True
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		ordering = ('name',)

