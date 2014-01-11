from django.db import models

class QueuedMail(models.Model):
	sender = models.EmailField(max_length=100, null=False, blank=False)
	receiver = models.EmailField(max_length=100, null=False, blank=False)
	# We store the raw MIME message, so if there are any attachments or
	# anything, we just push them right in there!
	fullmsg = models.TextField(null=False, blank=False)

	def __unicode__(self):
		return "%s: %s -> %s" % (self.pk, self.sender, self.receiver)
