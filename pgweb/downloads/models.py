from django.db import models
from django.contrib.auth.models import User
from pgweb.util.bases import PgModel

from pgweb.core.models import Organisation

from datetime import datetime

class Category(models.Model):
	catname = models.CharField(max_length=100, null=False, blank=False)
	blurb = models.TextField(null=False, blank=True)

	def __unicode__(self):
		return self.catname

class LicenceType(models.Model):
	typename = models.CharField(max_length=100, null=False, blank=False)

	def __unicode__(self):
		return self.typename

class Product(PgModel, models.Model):
	name = models.CharField(max_length=100, null=False, blank=False, unique=True)
	approved = models.BooleanField(null=False, default=False)
	publisher = models.ForeignKey(Organisation, null=False)
	url = models.URLField(null=False, blank=False)
	category = models.ForeignKey(Category, null=False)
	licencetype = models.ForeignKey(LicenceType, null=False)
	description = models.TextField(null=False, blank=False)
	price = models.CharField(max_length=100, null=False, blank=True)
	lastconfirmed = models.DateTimeField(null=False, blank=False, default=datetime.now())

	send_notification = True
	markdown_fields = ('description', )

	def __unicode__(self):
		return self.name

	def verify_submitter(self, user):
		return (user == self.publisher.submitter)

	class Meta:
		ordering = ('name',)
