from django.db import models

from pgweb.core.models import Organisation

class ProfessionalService(models.Model):
    approved = models.BooleanField(null=False, blank=False, default=False)

    org =  models.OneToOneField(Organisation, null=False, blank=False,
                            db_column="organisation_id",
                            verbose_name="organisation",
                            help_text="If no organisations are listed, please check the <a href=\"/account/orglist/\">organisation list</a> and contact the organisation manager or <a href=\"mailto:webmaster@postgresql.org\">webmaster@postgresql.org</a> if none are listed.")
    description = models.TextField(null=False,blank=False)
    employees = models.CharField(max_length=32, null=True, blank=True)
    locations = models.CharField(max_length=128, null=True, blank=True)
    region_africa = models.BooleanField(null=False, default=False, verbose_name="Africa")
    region_asia = models.BooleanField(null=False, default=False, verbose_name="Asia")
    region_europe = models.BooleanField(null=False, default=False, verbose_name="Europe")
    region_northamerica = models.BooleanField(null=False, default=False, verbose_name="North America")
    region_oceania = models.BooleanField(null=False, default=False, verbose_name="Oceania")
    region_southamerica = models.BooleanField(null=False, default=False, verbose_name="South America")
    hours = models.CharField(max_length=128, null=True, blank=True)
    languages = models.CharField(max_length=128, null=True, blank=True)
    customerexample = models.TextField(blank=True, null=True, verbose_name="Customer Example")
    experience = models.TextField(blank=True, null=True)
    contact = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=128, null=True, blank=True, verbose_name="URL")
    provides_support = models.BooleanField(null=False, default=False)
    provides_hosting = models.BooleanField(null=False, default=False)
    interfaces = models.CharField(max_length=512, null=True, blank=True, verbose_name="Interfaces (for hosting)")

    purge_urls = ('/support/professional_', )

    send_notification = True

    def verify_submitter(self, user):
        return (len(self.org.managers.filter(pk=user.pk)) == 1)

    def __unicode__(self):
        return self.org.name

    class Meta:
        ordering = ('org__name',)
