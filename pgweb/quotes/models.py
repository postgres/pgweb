from django.db import models


class Quote(models.Model):
    approved = models.BooleanField(null=False, default=False)
    quote = models.TextField(null=False, blank=False)
    who = models.CharField(max_length=100, null=False, blank=False)
    org = models.CharField(max_length=100, null=False, blank=False)
    link = models.URLField(null=False, blank=False)

    send_notification = True

    purge_urls = ('/about/quotesarchive/', '/$', )

    def __str__(self):
        if len(self.quote) > 75:
            return "%s..." % self.quote[:75]
        else:
            return self.quote
