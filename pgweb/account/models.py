from django.db import models
from django.contrib.auth.models import User

class CommunityAuthSite(models.Model):
	name = models.CharField(max_length=100, null=False, blank=False,
							help_text="Note that the value in this field is shown on the login page, so make sure it's user-friendly!")
	redirecturl = models.URLField(max_length=200, null=False, blank=False)
	cryptkey = models.CharField(max_length=100, null=False, blank=False,
								help_text="Use tools/communityauth/generate_cryptkey.py to create a key")
	comment = models.TextField(null=False, blank=True)
	cooloff_hours = models.IntegerField(null=False, blank=False, default=0,
										help_text="Number of hours a user must have existed in the systems before allowed to log in to this site")

	def __unicode__(self):
		return self.name

class EmailChangeToken(models.Model):
	user = models.ForeignKey(User, null=False, blank=False, unique=True)
	email = models.EmailField(max_length=75, null=False, blank=False)
	token = models.CharField(max_length=100, null=False, blank=False)
	sentat = models.DateTimeField(null=False, blank=False, auto_now=True)
