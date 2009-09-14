from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save

class Version(models.Model):
	tree = models.DecimalField(max_digits=3, decimal_places=1, null=False, blank=False)
	latestminor = models.IntegerField(null=False, blank=False, default=0)
	reldate = models.DateField(null=False, blank=False)
	relnotes = models.CharField(max_length=32, null=False, blank=False)

	def __unicode__(self):
		return "%s.%s" % (self.tree, self.latestminor)

	class Meta:
		ordering = ('-tree', )


class Country(models.Model):
	name = models.CharField(max_length=100, null=False, blank=False)
	tld = models.CharField(max_length=3, null=False, blank=False)

	class Meta:
		db_table = 'countries'
		ordering = ('name',)
		verbose_name = 'Country'
		verbose_name_plural = 'Countries'

	def __unicode__(self):
		return self.name

