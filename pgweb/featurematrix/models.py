from django.db import models

from pgweb.util.bases import PgModel

choices_map = {
 0: {'str': 'No',       'class': 'no', 'bgcolor': '#ffdddd'},
 1: {'str': 'Yes',      'class': 'yes', 'bgcolor': '#ddffdd'},
 2: {'str': 'Obsolete', 'class': 'obs', 'bgcolor': '#ddddff'},
 3: {'str': '?',        'class': 'unk', 'bgcolor': '#ffffaa'},
}
choices = [(k, v['str']) for k,v in choices_map.items()]

class FeatureGroup(PgModel, models.Model):
	groupname = models.CharField(max_length=100, null=False, blank=False)
	groupsort = models.IntegerField(null=False, blank=False)

	purge_urls = ('/about/featurematrix/', )

	def __unicode__(self):
		return self.groupname

	@property
	def columns(self):
		# Return a list of all the columns for the matrix
		return [b for a,b in versions]

class FeatureMatrixField(models.IntegerField):
	def __init__(self, verbose_name, visible_default=True):
		super(FeatureMatrixField, self).__init__(null=False, blank=False, default=0, verbose_name=verbose_name, choices=choices)
		self.visible_default = visible_default

class Feature(PgModel, models.Model):
	group = models.ForeignKey(FeatureGroup, null=False, blank=False)
	featurename = models.CharField(max_length=100, null=False, blank=False)
	featuredescription = models.TextField(null=False, blank=True)
	#WARNING! All fields that start with "v" will be considered versions!
	v74 = FeatureMatrixField(verbose_name="7.4", visible_default=False)
	v80 = FeatureMatrixField(verbose_name="8.0")
	v81 = FeatureMatrixField(verbose_name="8.1")
	v82 = FeatureMatrixField(verbose_name="8.2")
	v83 = FeatureMatrixField(verbose_name="8.3")
	v84 = FeatureMatrixField(verbose_name="8.4")
	v90 = FeatureMatrixField(verbose_name="9.0")
	v91 = FeatureMatrixField(verbose_name="9.1")
	v92 = FeatureMatrixField(verbose_name="9.2")
	v93 = FeatureMatrixField(verbose_name="9.3")
	v94 = FeatureMatrixField(verbose_name="9.4")

	purge_urls = ('/about/featurematrix/.*', )

	def __unicode__(self):
		# To make it look good in the admin interface, just don't render it
		return ''

	def columns(self):
		return [choices_map[getattr(self, a)] for a,b in versions]

	@property
	def featurelink(self):
		if self.featuredescription.startswith('http://'):
			return self.featuredescription
		else:
			return 'detail/%s/' % self.id

versions = [(f.name,f.verbose_name) for f in Feature()._meta.fields if f.name.startswith('v') and f.visible_default]

