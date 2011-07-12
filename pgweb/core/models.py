from django.db import models
from django.contrib.auth.models import User
from pgweb.util.bases import PgModel

from datetime import datetime

class Version(models.Model):
	tree = models.DecimalField(max_digits=3, decimal_places=1, null=False, blank=False)
	latestminor = models.IntegerField(null=False, blank=False, default=0)
	reldate = models.DateField(null=False, blank=False)
	relnotes = models.CharField(max_length=32, null=False, blank=False)
	current = models.BooleanField(null=False, blank=False, default=False)
	supported = models.BooleanField(null=False, blank=False, default=True)

	def __unicode__(self):
		return self.versionstring

	@property
	def versionstring(self):
		return "%s.%s" % (self.tree, self.latestminor)

	def save(self):
		# Make sure only one version at a time can be the current one.
		# (there may be some small race conditions here, but the likelyhood
		# that two admins are editing the version list at the same time...)
		if self.current:
			previous = Version.objects.filter(current=True)
			for p in previous:
				if not p == self:
					p.current = False
					p.save() # primary key check avoids recursion

		# Now that we've made any previously current ones non-current, we are
		# free to save this one.
		super(Version, self).save()

	class Meta:
		ordering = ('-tree', )

	def purge_urls(self):
		yield '/$'
		yield 'versions.rss'
		# FIXME: probably a lot more?


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

class OrganisationType(models.Model):
	typename = models.CharField(max_length=32, null=False, blank=False)

	def __unicode__(self):
		return self.typename

class Organisation(PgModel, models.Model):
	name = models.CharField(max_length=100, null=False, blank=False, unique=True)
	approved = models.BooleanField(null=False, default=False)
	address = models.TextField(null=False, blank=True)
	url = models.URLField(null=False, blank=False)
	email = models.EmailField(null=False, blank=True)
	phone = models.CharField(max_length=100, null=False, blank=True)
	orgtype = models.ForeignKey(OrganisationType, null=False, blank=False)
	managers = models.ManyToManyField(User, null=False, blank=False)
	lastconfirmed = models.DateTimeField(null=False, blank=False, default=datetime.now())

	send_notification = True

	def __unicode__(self):
		return self.name

	class Meta:
		ordering = ('name',)


# Basic classes for importing external RSS feeds, such as planet
class ImportedRSSFeed(models.Model):
	internalname = models.CharField(max_length=32, null=False, blank=False, unique=True)
	url = models.URLField(null=False, blank=False)

	def __unicode__(self):
		return self.internalname

class ImportedRSSItem(models.Model):
	feed = models.ForeignKey(ImportedRSSFeed)
	title = models.CharField(max_length=100, null=False, blank=False)
	url = models.URLField(null=False, blank=False)
	posttime = models.DateTimeField(null=False, blank=False)

	def __unicode__(self):
		return self.title

	@property
	def date(self):
		return self.posttime.strftime("%Y-%m-%d")

