from django.db import models
from django.contrib.auth.models import User
from pgweb.util.bases import PgModel
from pgweb.util.misc import varnish_purge

from datetime import datetime

class Version(PgModel, models.Model):
	tree = models.DecimalField(max_digits=3, decimal_places=1, null=False, blank=False)
	latestminor = models.IntegerField(null=False, blank=False, default=0, help_text="For beta versions, latestminor means latest beta number. For other releases, it's the latest minor release number in the tree.")
	reldate = models.DateField(null=False, blank=False)
	relnotes = models.CharField(max_length=32, null=False, blank=False)
	current = models.BooleanField(null=False, blank=False, default=False)
	supported = models.BooleanField(null=False, blank=False, default=True)
	beta = models.BooleanField(null=False, blank=False, default=False, help_text="For beta versions, latestminor means beta number")
	docsloaded = models.DateTimeField(null=True, blank=True, help_text="The timestamp of the latest docs load. Used to control indexing and info on developer docs.")
	firstreldate = models.DateField(null=False, blank=False, help_text="The date of the .0 release in this tree")
	eoldate = models.DateField(null=False, blank=False, help_text="The planned EOL date for this tree")

	def __unicode__(self):
		return self.versionstring

	@property
	def versionstring(self):
		if not self.beta:
			return "%s.%s" % (self.tree, self.latestminor)
		else:
			return "%sbeta%s" % (self.tree, self.latestminor)

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
		yield '/support/submitbug'
		yield '/support/versioning'
		yield '/versions.rss'


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

class Language(models.Model):
	# Import data from http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
	# (yes, there is a UTF16 BOM in the UTF8 file)
	# (and yes, there is a 7 length value in a field specified as 3 chars)
	alpha3 = models.CharField(max_length=7, null=False, blank=False, primary_key=True)
	alpha3term = models.CharField(max_length=3, null=False, blank=True)
	alpha2 = models.CharField(max_length=2, null=False, blank=True)
	name = models.CharField(max_length=100, null=False, blank=False)
	frenchname = models.CharField(max_length=100, null=False, blank=False)

	class Meta:
		ordering = ('name', )

	def __unicode__(self):
		return self.name

	# Get the english language to use for default in foreign keys
	@staticmethod
	def english():
		return Language.objects.get(pk='eng')

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
	orgtype = models.ForeignKey(OrganisationType, null=False, blank=False, verbose_name="Organisation type")
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
	purgepattern = models.CharField(max_length=512, null=False, blank=True, help_text="NOTE! Pattern will be automatically anchored with ^ at the beginning, but you must lead with a slash in most cases - and don't forget to include the trailing $ in most cases")

	def purge_related(self):
		if self.purgepattern:
			varnish_purge(self.purgepattern)

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


# Extra attributes for users (if they have them)
class UserProfile(models.Model):
	user = models.ForeignKey(User, null=False, blank=False, unique=True, primary_key=True)
	sshkey = models.TextField(null=False, blank=True, verbose_name="SSH key", help_text= "Paste one or more public keys in OpenSSH format, one per line.")
	lastmodified = models.DateTimeField(null=False, blank=False, auto_now=True)

# Notifications sent for any moderated content.
# Yes, we uglify it by storing the type of object as a string, so we don't
# end up with a bazillion fields being foreign keys. Ugly, but works.
class ModerationNotification(models.Model):
	objectid = models.IntegerField(null=False, blank=False, db_index=True)
	objecttype = models.CharField(null=False, blank=False, max_length=100)
	text = models.TextField(null=False, blank=False)
	author = models.CharField(null=False,  blank=False, max_length=100)
	date = models.DateTimeField(null=False, blank=False, auto_now=True)

	def __unicode__(self):
		return "%s id %s (%s): %s" % (self.objecttype, self.objectid, self.date, self.text[:50])

	class Meta:
		ordering = ('-date', )
