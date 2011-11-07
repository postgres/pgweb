from django.db import models
from django.contrib.auth.models import User
from pgweb.util.bases import PgModel

from pgweb.core.models import Organisation

from datetime import datetime

class Mirror(models.Model):
	country_name = models.CharField(max_length=50, null=False, blank=False)
	country_code = models.CharField(max_length=2, null=False, blank=False)
	mirror_created = models.DateTimeField(null=False, blank=False, default=datetime.now())
	mirror_last_rsync = models.DateTimeField(null=False, blank=False, default=datetime(1970,1,1))
	mirror_index = models.IntegerField(null=False)
	host_addr = models.IPAddressField(null=True, default='0.0.0.0')
	host_path = models.CharField(max_length=100, null=True)
	host_sponsor = models.CharField(max_length=100, null=True)
	host_contact = models.CharField(max_length=100, null=True)
	host_email = models.CharField(max_length=100, null=True)
	host_notes = models.TextField(null=True)
	rsync_host1 = models.CharField(max_length=100, null=True)
	rsync_host2 = models.CharField(max_length=100, null=True)
	mirror_active = models.BooleanField(null=False, default=True)
	mirror_dns = models.BooleanField(null=False, default=False)
	mirror_private = models.BooleanField(null=False, default=False)
	host_use_cname = models.BooleanField(null=False, default=False)
	host_cname_host = models.CharField(max_length=100, null=True)
	mirror_primary = models.BooleanField(null=False, default=False)
	error_count = models.IntegerField(null=False, default=0)
	alternate_protocol = models.BooleanField(null=False, default=False)
	alternate_at_root = models.BooleanField(null=False, default=False)

	class Meta:
		db_table='mirrors'

	def __unicode__(self):
		return "%s.%s" % (self.country_code, self.mirror_index)

	def get_host_name(self):
		if self.mirror_index == 0:
			return "ftp.%s.postgresql.org" % self.country_code
		else:
			return "ftp%s.%s.postgresql.org" % (self.mirror_index, self.country_code)

	def get_root_path(self, method):
		if method == 'f' or not self.alternate_at_root:
			# FTP method, or http with same path, build complete one
			return ("%s/%s" % (self.get_host_name(), self.host_path)).replace('//','/').rstrip('/')
		else:
			# http with alternate_at_root - thus, ignore the path element
			return self.get_host_name()

	def get_all_protocols(self):
		if self.alternate_protocol:
			return ('ftp', 'http', )
		else:
			return ('ftp', )

class Category(models.Model):
	catname = models.CharField(max_length=100, null=False, blank=False)
	blurb = models.TextField(null=False, blank=True)

	def __unicode__(self):
		return self.catname

	class Meta:
		ordering = ('catname',)

class LicenceType(models.Model):
	typename = models.CharField(max_length=100, null=False, blank=False)

	def __unicode__(self):
		return self.typename

	class Meta:
		ordering = ('typename',)

class Product(PgModel, models.Model):
	name = models.CharField(max_length=100, null=False, blank=False, unique=True)
	approved = models.BooleanField(null=False, default=False)
	publisher = models.ForeignKey(Organisation, null=False)
	url = models.URLField(null=False, blank=False)
	category = models.ForeignKey(Category, null=False)
	licencetype = models.ForeignKey(LicenceType, null=False, verbose_name="Licence type")
	description = models.TextField(null=False, blank=False)
	price = models.CharField(max_length=200, null=False, blank=True)
	lastconfirmed = models.DateTimeField(null=False, blank=False, default=datetime.now())

	send_notification = True
	markdown_fields = ('description', )

	def __unicode__(self):
		return self.name

	def verify_submitter(self, user):
		return (len(self.publisher.managers.filter(pk=user.pk)) == 1)

	class Meta:
		ordering = ('name',)

class StackBuilderApp(models.Model):
	textid = models.CharField(max_length=100, null=False, blank=False)
	version = models.CharField(max_length=20, null=False, blank=False)
	platform = models.CharField(max_length=20, null=False, blank=False,
		choices= (('windows', 'Windows'), ('osx', 'Mac OS X'),
			('linux', 'Linux (32-bit)'), ('linux-x64', 'Linux (64-bit)'))
	)
	name = models.CharField(max_length=500, null=False, blank=False)
	active = models.BooleanField(null=False, blank=False, default=True)
	description = models.TextField(null=False, blank=False)
	category = models.CharField(max_length=100, null=False, blank=False)
	pgversion = models.CharField(max_length=5, null=False, blank=True)
	edbversion = models.CharField(max_length=5, null=False, blank=True)
	format = models.CharField(max_length=5, null=False, blank=False,
		choices = (('bin', 'Linux .bin'), ('app', 'Mac .app'),
			   ('pkg', 'Mac .pkg'), ('mpkg', 'Mac .mpkg'),
			   ('exe', 'Windows .exe'), ('msi', 'Windows .msi'))
	)
	installoptions = models.CharField(max_length=500, null=False, blank=True)
	upgradeoptions = models.CharField(max_length=500, null=False, blank=True)
	checksum = models.CharField(max_length=32, null=False, blank=False)
	mirrorpath = models.CharField(max_length=500, null=False, blank=True)
	alturl = models.URLField(max_length=500, null=False, blank=True)
	dependencies = models.ManyToManyField("self", blank=True)
	versionkey = models.CharField(max_length=500, null=False, blank=False)

	def __unicode__(self):
		return "%s %s %s" % (self.textid, self.version, self.platform)

	class Meta:
		unique_together = ('textid', 'version', 'platform', )
		ordering = ('textid', 'name', 'platform', )

