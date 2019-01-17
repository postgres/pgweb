from django.db import models

class BugIdMap(models.Model):
    # Explicit id field because we don't want a SERIAL here, since we generate
    # the actual bug IDs externally.
    id = models.IntegerField(null=False, blank=False, primary_key=True)
    messageid = models.CharField(max_length=500, null=False, blank=False)
