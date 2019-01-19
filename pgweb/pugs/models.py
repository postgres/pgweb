from django.db import models


class PUG(models.Model):
    """
    contains information about a local PostgreSQL user group
    """
    country = models.ForeignKey('core.Country')
    org = models.ForeignKey('core.Organisation', null=True, blank=True, help_text='Organisation that manages the PUG and its contents')
    approved = models.BooleanField(null=False, blank=False, default=False)
    locale = models.CharField(max_length=255, help_text="Locale where the PUG meets, e.g. 'New York City'")
    title = models.CharField(max_length=255, help_text="Title/Name of the PUG, e.g. 'NYC PostgreSQL User Group'")
    website_url = models.TextField(null=True, blank=True)
    mailing_list_url = models.TextField(null=True, blank=True)

    purge_urls = ('/community/user-groups/', )
    send_notification = True

    def __str__(self):
        return self.title
