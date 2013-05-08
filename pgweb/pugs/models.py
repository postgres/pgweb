from django.db import models
from pgweb.util.bases import PgModel

class PUG(PgModel, models.Model):
    """
    contains information about a local PostgreSQL user group
    """
    country = models.ForeignKey('core.Country')
    org = models.ForeignKey('core.Organisation', null=True, blank=True, help_text='Organization that manages the PUG and its contents')
    approved = models.BooleanField(null=False, blank=False, default=False)
    locale = models.CharField(max_length=255, help_text="Locale where the PUG meets, e.g. 'New York City'")
    title = models.CharField(max_length=255, help_text="Title/Name of the PUG, e.g. 'NYC PostgreSQL User Group'")
    website_url = models.TextField(null=True, blank=True)
    mailing_list_url = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return self.title
