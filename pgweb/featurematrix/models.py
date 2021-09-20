from django.db import models

choices_map = {
    0: {'str': 'No', 'class': 'no', 'bgcolor': '#ffdddd'},
    1: {'str': 'Yes', 'class': 'yes', 'bgcolor': '#ddffdd'},
    2: {'str': 'Obsolete', 'class': 'obs', 'bgcolor': '#ddddff'},
    3: {'str': '?', 'class': 'unk', 'bgcolor': '#ffffaa'},
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
    v14 = models.IntegerField(verbose_name="13", null=False, blank=False, default=0, choices=choices)

    purge_urls = ('/about/featurematrix/.*', )

    def __str__(self):
        # To make it look good in the admin interface, just don't render it
        return ''

    def columns(self):
        # Get a list of column based on all versions that are visible_default
        return [choices_map[getattr(self, a)] for a, b in versions]

    def featuredescription_is_url(self):
        """
        Returns true if the entirety of the feautre description is a URL, or
        at least gives off the appearance that it is.
        """
        return self.featuredescription.startswith('https://') or self.featuredescription.startswith('http://')

    @property
    def featurelink(self):
        if self.featuredescription_is_url():
            return self.featuredescription
        else:
            return 'detail/%s/' % self.id


versions = [(f.name, f.verbose_name) for f in Feature()._meta.fields if f.name.startswith('v') and getattr(f, 'visible_default', True)]
versions = sorted(versions, key=lambda f: -float(f[1]))
