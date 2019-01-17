from django.db import models
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
            return str(self.version.numtree)

    class Meta:
        db_table = 'docs'
        # Index file first, because we want to list versions by file
        unique_together = [('file', 'version')]

class DocPageAlias(models.Model):
    file1 = models.CharField(max_length=64, null=False, blank=False, unique=True)
    file2 = models.CharField(max_length=64, null=False, blank=False, unique=True)

    def __unicode__(self):
        return u"%s <-> %s" % (self.file1, self.file2)

    # XXX: needs a unique functional index as well, see the migration!
    class Meta:
        db_table = 'docsalias'
        verbose_name_plural='Doc page aliases'
