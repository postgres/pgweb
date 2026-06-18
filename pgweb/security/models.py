from django.db import models
from django.core.validators import ValidationError, RegexValidator

import re

from pgweb.core.models import Version
from pgweb.news.models import NewsArticle
from pgweb.security.validators import CvssValidator

import cvss

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


def make_cvenumber(cve):
    """
    creates a ``cvenumber`` from a CVE ID string (e.g. YYYY-DDDDD).

    raises a validation error if the CVE ID string is invalid
    """
    m = re_cve.match(cve)
    if not m:
        raise ValidationError("Invalid CVE")
    return 100000 * int(m.groups(0)[0]) + int(m.groups(0)[1])


class SecurityPatch(models.Model):
    public = models.BooleanField(null=False, blank=False, default=False)
    newspost = models.ForeignKey(NewsArticle, null=True, blank=True, on_delete=models.CASCADE)
    cve = models.CharField(max_length=32, null=False, blank=True, validators=[cve_validator, ])
    cvenumber = models.IntegerField(null=False, blank=False, db_index=True)
    detailslink = models.URLField(null=False, blank=True)
    description = models.TextField(null=False, blank=False)
    details = models.TextField(blank=True, null=True, help_text="Additional details about the security patch")
    component = models.CharField(max_length=32, null=False, blank=False, help_text="If multiple components, choose the most critical one", choices=component_choices)

    versions = models.ManyToManyField(Version, through='SecurityPatchVersion')

    vector = models.CharField(max_length=100, null=False, blank=True, verbose_name="CVSS vector", validators=[
        RegexValidator('^CVSS:3.1/AV:(.)/AC:(.)/PR:(.)/UI:(.)/S:(.)/C:(.)/I:(.)/A:(.)$', 'Enter a valid CVSS vector, including version (3.1)'),
        CvssValidator,
    ])

    legacyscore = models.CharField(max_length=1, null=False, blank=True, verbose_name='Legacy score', choices=(('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')))

    def purge_urls(self):
        yield '/support/security/CVE-%s/' % self.cve
        yield '/support/security/'

    def save(self, force_insert=False, force_update=False):
        # Calculate a number from the CVE, that we can use to sort by. We need to
        # do this, because CVEs can have 4 or 5 digit second parts...
        if self.cve == '':
            self.cvenumber = 0
        else:
            # note that the make_cvenumber function can raise a validation error
            # if the value of CVE is not a valid CVE identifier
            self.cvenumber = make_cvenumber(self.cve)
        super(SecurityPatch, self).save(force_insert, force_update)

    def __str__(self):
        return self.cve

    @property
    def cvssvector(self):
        if not self.vector:
            return None
        return self.vector.split('/', 1)[1]  # Strip out the CVSS version (for now)

    @property
    def cvssscore(self):
        try:
            c = cvss.CVSS3(self.vector)
            return c.base_score
        except Exception:
            return -1

    class Meta:
        verbose_name_plural = 'Security patches'
        ordering = ('-cvenumber',)


class SecurityPatchVersion(models.Model):
    patch = models.ForeignKey(SecurityPatch, null=False, blank=False, on_delete=models.CASCADE)
    version = models.ForeignKey(Version, null=False, blank=False, on_delete=models.CASCADE)
    fixed_minor = models.IntegerField(null=False, blank=False)
