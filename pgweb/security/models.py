from django.db import models
from django.core.validators import ValidationError

import re

from pgweb.core.models import Version
from pgweb.news.models import NewsArticle

import cvss

vector_choices = {k: list(v.items()) for k, v in list(cvss.constants3.METRICS_VALUE_NAMES.items())}

component_choices = (
    ('core server', 'Core server product'),
    ('client', 'Client library or application only'),
    ('contrib module', 'Contrib module only'),
    ('client contrib module', 'Client contrib module only'),
    ('packaging', 'Packaging, e.g. installers or RPM'),
    ('other', 'Other'),
)


re_cve = re.compile(r'^(\d{4})-(\d{4,7})$')


def cve_validator(val):
    if not re_cve.match(val):
        raise ValidationError("Enter CVE in format (YYYY-NNNN (up to 7 N) without the CVE text")


def other_vectors_validator(val):
    if val != val.upper():
        raise ValidationError("Vector must be uppercase")

    try:
        for vector in val.split('/'):
            k, v = vector.split(':')
            if k not in cvss.constants3.METRICS_VALUES:
                raise ValidationError("Metric {0} is unknown".format(k))
            if k in ('AV', 'AC', 'PR', 'UI', 'S', 'C', 'I', 'A'):
                raise ValidationError("Metric {0} must be specified in the dropdowns".format(k))
            if v not in cvss.constants3.METRICS_VALUES[k]:
                raise ValidationError("Metric {0} has unknown value {1}. Valind ones are: {2}".format(
                    k, v,
                    ", ".join(list(cvss.constants3.METRICS_VALUES[k].keys())),
                ))
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError("Failed to parse vectors: %s" % e)


class SecurityPatch(models.Model):
    public = models.BooleanField(null=False, blank=False, default=False)
    newspost = models.ForeignKey(NewsArticle, null=True, blank=True, on_delete=models.CASCADE)
    cve = models.CharField(max_length=32, null=False, blank=True, validators=[cve_validator, ])
    cve_visible = models.BooleanField(null=False, blank=False, default=False)
    cvenumber = models.IntegerField(null=False, blank=False, db_index=True)
    detailslink = models.URLField(null=False, blank=True)
    description = models.TextField(null=False, blank=False)
    component = models.CharField(max_length=32, null=False, blank=False, help_text="If multiple components, choose the most critical one", choices=component_choices)

    versions = models.ManyToManyField(Version, through='SecurityPatchVersion')

    vector_av = models.CharField(max_length=1, null=False, blank=True, verbose_name="Attack Vector", choices=vector_choices['AV'])
    vector_ac = models.CharField(max_length=1, null=False, blank=True, verbose_name="Attack Complexity", choices=vector_choices['AC'])
    vector_pr = models.CharField(max_length=1, null=False, blank=True, verbose_name="Privileges Required", choices=vector_choices['PR'])
    vector_ui = models.CharField(max_length=1, null=False, blank=True, verbose_name="User Interaction", choices=vector_choices['UI'])
    vector_s = models.CharField(max_length=1, null=False, blank=True, verbose_name="Scope", choices=vector_choices['S'])
    vector_c = models.CharField(max_length=1, null=False, blank=True, verbose_name="Confidentiality Impact", choices=vector_choices['C'])
    vector_i = models.CharField(max_length=1, null=False, blank=True, verbose_name="Integrity Impact", choices=vector_choices['I'])
    vector_a = models.CharField(max_length=1, null=False, blank=True, verbose_name="Availability Impact", choices=vector_choices['A'])
    legacyscore = models.CharField(max_length=1, null=False, blank=True, verbose_name='Legacy score', choices=(('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')))

    purge_urls = ('/support/security/', )

    def save(self, force_insert=False, force_update=False):
        # Calculate a number from the CVE, that we can use to sort by. We need to
        # do this, because CVEs can have 4 or 5 digit second parts...
        if self.cve == '':
            self.cvenumber = 0
        else:
            m = re_cve.match(self.cve)
            if not m:
                raise ValidationError("Invalid CVE, should not get here!")
            self.cvenumber = 100000 * int(m.groups(0)[0]) + int(m.groups(0)[1])
        super(SecurityPatch, self).save(force_insert, force_update)

    def __str__(self):
        return self.cve

    @property
    def cvssvector(self):
        if not self.vector_av:
            return None
        s = 'AV:{0}/AC:{1}/PR:{2}/UI:{3}/S:{4}/C:{5}/I:{6}/A:{7}'.format(
            self.vector_av, self.vector_ac, self.vector_pr, self.vector_ui,
            self.vector_s, self.vector_c, self.vector_i, self.vector_a)
        return s

    @property
    def cvssscore(self):
        try:
            c = cvss.CVSS3("CVSS:3.0/" + self.cvssvector)
            return c.base_score
        except Exception:
            return -1

    @property
    def cvelink(self):
        return "https://access.redhat.com/security/cve/CVE-{0}".format(self.cve)

    class Meta:
        verbose_name_plural = 'Security patches'
        ordering = ('-cvenumber',)


class SecurityPatchVersion(models.Model):
    patch = models.ForeignKey(SecurityPatch, null=False, blank=False, on_delete=models.CASCADE)
    version = models.ForeignKey(Version, null=False, blank=False, on_delete=models.CASCADE)
    fixed_minor = models.IntegerField(null=False, blank=False)
