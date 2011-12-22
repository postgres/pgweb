from django.db import models

class CommunityAuthSite(models.Model):
	name = models.CharField(max_length=100, null=False, blank=False)
	redirecturl = models.URLField(max_length=200, null=False, blank=False)
	cryptkey = models.CharField(max_length=100, null=False, blank=False,
								help_text="Use tools/communityauth/generate_cryptkey.py to create a key")
	comment = models.TextField(null=False, blank=True)

	def __unicode__(self):
		return self.name
