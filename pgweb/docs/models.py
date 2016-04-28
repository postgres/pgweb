from django.db import models
from django.contrib.auth.models import User
from pgweb.core.models import Version

class DocPage(models.Model):
	id = models.AutoField(null=False, primary_key=True)
	file = models.CharField(max_length=64, null=False, blank=False)
	version = models.ForeignKey(Version, null=False, blank=False, db_column='version', to_field='tree')
	title = models.CharField(max_length=256, null=True, blank=True)
	content = models.TextField(null=True, blank=True)

	def display_version(self):
		"""Version as used for displaying and in URLs"""
		if self.version.tree == 0:
			return 'devel'
		else:
			return str(self.version.tree)

	class Meta:
		db_table = 'docs'
		# Index file first, because we want to list versions by file
		unique_together = [('file', 'version')]

class DocComment(models.Model):
	version = models.DecimalField(max_digits=3, decimal_places=1, null=False)
	file = models.CharField(max_length=64, null=False, blank=False)
	comment = models.TextField(null=False, blank=False)
	posted_at = models.DateTimeField(null=False, blank=False, auto_now_add=True)
	submitter = models.ForeignKey(User, null=False)
	approved = models.BooleanField(blank=False, default=False)

	send_notification = True

	def purge_urls(self):
		yield '/docs/%s/interactive/%s' % (self.version, self.file)
		try:
			if Version.objects.get(tree=self.version).current:
				yield '/docs/current/interactive/%s' % self.file
		except Version.DoesNotExist:
			pass

	class Meta:
		ordering = ('-posted_at',)

	@property
	def poster(self):
		if self.submitter_id > 0:
			return "%s %s" % (self.submitter.first_name, self.submitter.last_name)
		else:
			return ''

	def __unicode__(self):
		return "%s ver %s: %s" % (self.file, self.version, self.comment[:50])
