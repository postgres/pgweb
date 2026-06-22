from django.db import models
from django.db.models import Func, F, Value
from django.db.models.functions import Cast
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

cve_regexp = r'^\d{4}-\d{4,5}$'
cvss_vector_regexp = r'^CVSS:3.1/AV:(.)/AC:(.)/PR:(.)/UI:(.)/S:(.)/C:(.)/I:(.)/A:(.)$'


class SecurityPatch(models.Model):
    public = models.BooleanField(null=False, blank=False, default=False)
    newspost = models.ForeignKey(NewsArticle, null=True, blank=True, on_delete=models.CASCADE)
    cve = models.CharField(max_length=32, null=False, blank=True, unique=True, validators=[
        RegexValidator(cve_regexp, 'Enter CVE in format (YYYY-NNNNN (up to 5 N) without the CVE text'),
    ])
    cvenumber = models.GeneratedField(
        expression=(
            Cast(Func(F('cve'), Value('-'), Value(1), function='split_part'), output_field=models.IntegerField()) * 100000 +
            Cast(Func(F('cve'), Value('-'), Value(2), function='split_part'), output_field=models.IntegerField())
        ),
        output_field=models.IntegerField(),
        db_persist=True,
        unique=True,
    )
    detailslink = models.URLField(null=False, blank=True)
    description = models.TextField(null=False, blank=False)
    details = models.TextField(blank=True, null=True, help_text="Additional details about the security patch")
    component = models.CharField(max_length=32, null=False, blank=False, help_text="If multiple components, choose the most critical one", choices=component_choices)

    versions = models.ManyToManyField(Version, through='SecurityPatchVersion')

    vector = models.CharField(max_length=100, null=False, blank=True, verbose_name="CVSS vector", validators=[
        RegexValidator(cvss_vector_regexp, 'Enter a valid CVSS vector, including version (3.1)'),
        CvssValidator,
    ])

    legacyscore = models.CharField(max_length=1, null=False, blank=True, verbose_name='Legacy score', choices=(('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')))

    def purge_urls(self):
        yield '/support/security/CVE-%s/' % self.cve
        yield '/support/security/'

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
        constraints = (
            models.CheckConstraint(
                name='validate_cve_format',
                condition=Func(F('cve'), Value(cve_regexp), function='regexp_like', output_field=models.BooleanField()),
            ),
            models.CheckConstraint(
                name='validate_cvss_vector',
                condition=models.Q(vector="") | Func(F('vector'), Value(cvss_vector_regexp), function='regexp_like', output_field=models.BooleanField()),
            ),
            models.CheckConstraint(
                name='validate_component',
                condition=models.Q(component__in=[c[0] for c in component_choices]),
            )
        )


class SecurityPatchVersion(models.Model):
    patch = models.ForeignKey(SecurityPatch, null=False, blank=False, on_delete=models.CASCADE, db_index=True)
    version = models.ForeignKey(Version, null=False, blank=False, on_delete=models.CASCADE, db_index=True)
    fixed_minor = models.IntegerField(null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(name="unique_patch_version", fields=['patch', 'version']),
        ]
