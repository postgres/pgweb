from django.db import models

class CommunityAuthSite(models.Model):
	name = models.CharField(max_length=100, null=False, blank=False,
							help_text="Note that the value in this field is shown on the login page, so make sure it's user-friendly!")
	redirecturl = models.URLField(max_length=200, null=False, blank=False)
	cryptkey = models.CharField(max_length=100, null=False, blank=False,
								help_text="Use tools/communityauth/generate_cryptkey.py to create a key")
	comment = models.TextField(null=False, blank=True)

	def __unicode__(self):
		return self.name
