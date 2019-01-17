from django.db import models
from django.contrib.auth.models import User


class CommunityAuthOrg(models.Model):
    orgname = models.CharField(max_length=100, null=False, blank=False,
                               help_text="Name of the organisation")
    require_consent = models.BooleanField(null=False, blank=False, default=True)

    def __unicode__(self):
        return self.orgname


class CommunityAuthSite(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False,
                            help_text="Note that the value in this field is shown on the login page, so make sure it's user-friendly!")
    redirecturl = models.URLField(max_length=200, null=False, blank=False)
    cryptkey = models.CharField(max_length=100, null=False, blank=False,
                                help_text="Use tools/communityauth/generate_cryptkey.py to create a key")
    comment = models.TextField(null=False, blank=True)
    org = models.ForeignKey(CommunityAuthOrg, null=False, blank=False)
    cooloff_hours = models.IntegerField(null=False, blank=False, default=0,
                                        help_text="Number of hours a user must have existed in the systems before allowed to log in to this site")

    def __unicode__(self):
        return self.name


class CommunityAuthConsent(models.Model):
    user = models.ForeignKey(User, null=False, blank=False)
    org = models.ForeignKey(CommunityAuthOrg, null=False, blank=False)
    consentgiven = models.DateTimeField(null=False, blank=False)

    class Meta:
        unique_together = (('user', 'org'), )


class EmailChangeToken(models.Model):
    user = models.OneToOneField(User, null=False, blank=False)
    email = models.EmailField(max_length=75, null=False, blank=False)
    token = models.CharField(max_length=100, null=False, blank=False)
    sentat = models.DateTimeField(null=False, blank=False, auto_now=True)
