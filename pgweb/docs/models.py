from django.db import models

class DocPage(models.Model):
	id = models.AutoField(null=False, primary_key=True)
	file = models.CharField(max_length=64, null=False, blank=False)
	version = models.DecimalField(max_digits=3, decimal_places=1, null=False)
	title = models.CharField(max_length=256, null=True, blank=True)
	content = models.TextField(null=True, blank=True)

	class Meta:
		db_table = 'docs'

