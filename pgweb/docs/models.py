from django.db import models
from pgweb.core.models import Version


class DocPage(models.Model):
    id = models.AutoField(null=False, primary_key=True)
    file = models.CharField(max_length=64, null=False, blank=False)
    version = models.ForeignKey(Version, null=False, blank=False, db_column='version', to_field='tree', on_delete=models.CASCADE)
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

    def __str__(self):
        return "%s <-> %s" % (self.file1, self.file2)

    # XXX: needs a unique functional index as well, see the migration!
    class Meta:
        db_table = 'docsalias'
        verbose_name_plural = 'Doc page aliases'


class DocPageRedirect(models.Model):
    """DocPageRedirect offers the ability to redirect from a page that has been
    completely removed from the PostgreSQL documentation
    """
    redirect_from = models.CharField(max_length=64, null=False, blank=False, unique=True, help_text='Page to redirect from, e.g. "old_page.html"')
    redirect_to = models.CharField(max_length=64, null=False, blank=False, unique=True, help_text='Page to redirect to, e.g. "new_page.html"')

    def __str__(self):
        return "%s => %s" % (self.redirect_from, self.redirect_to)

    class Meta:
        verbose_name_plural = "Doc page redirects"
