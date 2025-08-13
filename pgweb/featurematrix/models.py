from django.db import models

choices_map = {
    0: {'str': 'No', 'class': 'no'},
    1: {'str': 'Yes', 'class': 'yes'},
    2: {'str': 'Obsolete', 'class': 'obs'},
    3: {'str': '?', 'class': 'unk'},
}
choices = [(k, v['str']) for k, v in list(choices_map.items())]


class FeatureGroup(models.Model):
    groupname = models.CharField(max_length=100, null=False, blank=False)
    groupsort = models.IntegerField(null=False, blank=False)

    purge_urls = ('/about/featurematrix/', )

    def __str__(self):
        return self.groupname

    @property
    def columns(self):
        # Return a list of all the columns for the matrix
        return [b for a, b in versions]


class Feature(models.Model):
    group = models.ForeignKey(FeatureGroup, null=False, blank=False, on_delete=models.CASCADE)
    featurename = models.CharField(max_length=100, null=False, blank=False)
    featuredescription = models.TextField(null=False, blank=True, help_text="""Supports Markdown. A single, plain URL will link directly to that URL.""")
    # WARNING! All fields that start with "v" will be considered versions!
    v74 = models.IntegerField(verbose_name="7.4", null=False, blank=False, default=0, choices=choices)
    v74.visible_default = False
    v80 = models.IntegerField(verbose_name="8.0", null=False, blank=False, default=0, choices=choices)
    v80.visible_default = False
    v81 = models.IntegerField(verbose_name="8.1", null=False, blank=False, default=0, choices=choices)
    v82 = models.IntegerField(verbose_name="8.2", null=False, blank=False, default=0, choices=choices)
    v83 = models.IntegerField(verbose_name="8.3", null=False, blank=False, default=0, choices=choices)
    v84 = models.IntegerField(verbose_name="8.4", null=False, blank=False, default=0, choices=choices)
    v90 = models.IntegerField(verbose_name="9.0", null=False, blank=False, default=0, choices=choices)
    v91 = models.IntegerField(verbose_name="9.1", null=False, blank=False, default=0, choices=choices)
    v92 = models.IntegerField(verbose_name="9.2", null=False, blank=False, default=0, choices=choices)
    v93 = models.IntegerField(verbose_name="9.3", null=False, blank=False, default=0, choices=choices)
    v94 = models.IntegerField(verbose_name="9.4", null=False, blank=False, default=0, choices=choices)
    v95 = models.IntegerField(verbose_name="9.5", null=False, blank=False, default=0, choices=choices)
    v96 = models.IntegerField(verbose_name="9.6", null=False, blank=False, default=0, choices=choices)
    v10 = models.IntegerField(verbose_name="10", null=False, blank=False, default=0, choices=choices)
    v11 = models.IntegerField(verbose_name="11", null=False, blank=False, default=0, choices=choices)
    v12 = models.IntegerField(verbose_name="12", null=False, blank=False, default=0, choices=choices)
    v13 = models.IntegerField(verbose_name="13", null=False, blank=False, default=0, choices=choices)
    v14 = models.IntegerField(verbose_name="14", null=False, blank=False, default=0, choices=choices)
    v15 = models.IntegerField(verbose_name="15", null=False, blank=False, default=0, choices=choices)
    v16 = models.IntegerField(verbose_name="16", null=False, blank=False, default=0, choices=choices)
    v17 = models.IntegerField(verbose_name="17", null=False, blank=False, default=0, choices=choices)

    purge_urls = ('/about/featurematrix/.*', )

    def __str__(self):
        # To make it look good in the admin interface, just don't render it
        return ''
