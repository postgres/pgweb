from django.db import models
from django.contrib.auth.models import User


class CommunityAuthOrg(models.Model):
    orgname = models.CharField(max_length=100, null=False, blank=False,
                               help_text="Name of the organisation")
    require_consent = models.BooleanField(null=False, blank=False, default=True)

    def __str__(self):
        return self.orgname


class CommunityAuthSite(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False,
                            help_text="Note that the value in this field is shown on the login page, so make sure it's user-friendly!")
    redirecturl = models.URLField(max_length=200, null=False, blank=False)
    apiurl = models.URLField(max_length=200, null=False, blank=True)
    cryptkey = models.CharField(max_length=100, null=False, blank=False,
                                help_text="Use tools/communityauth/generate_cryptkey.py to create a key")
    comment = models.TextField(null=False, blank=True)
    org = models.ForeignKey(CommunityAuthOrg, null=False, blank=False, on_delete=models.CASCADE)
    cooloff_hours = models.IntegerField(null=False, blank=False, default=0,
                                        help_text="Number of hours a user must have existed in the systems before allowed to log in to this site")
    push_changes = models.BooleanField(null=False, blank=False, default=False,
                                       help_text="Supports receiving http POSTs with changes to accounts")
    push_ssh = models.BooleanField(null=False, blank=False, default=False,
                                   help_text="Wants to receive SSH keys in push changes")

    def __str__(self):
        return self.name


class CommunityAuthConsent(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    org = models.ForeignKey(CommunityAuthOrg, null=False, blank=False, on_delete=models.CASCADE)
    consentgiven = models.DateTimeField(null=False, blank=False)

    class Meta:
        unique_together = (('user', 'org'), )


class SecondaryEmail(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    email = models.EmailField(max_length=75, null=False, blank=False, unique=True)
    confirmed = models.BooleanField(null=False, blank=False, default=False)
    token = models.CharField(max_length=100, null=False, blank=False)
    sentat = models.DateTimeField(null=False, blank=False, auto_now=True)

    class Meta:
        ordering = ('email', )
