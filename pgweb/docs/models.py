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
